import math
from email.mime.application import MIMEApplication
from os.path import basename

import psycopg2
import psycopg2.errors
import logging
import asyncio
import sqlalchemy
import aiosmtplib

from pathlib import Path

from aiogram.types import Message, CallbackQuery

from src.models.models import *
from src.states.states import OperationStates
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


async def send_mail_async(ctx, preset_id: int, files: list):
    text_type = 'plain'
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        try:
            _data = session.execute(
                select(EmailsPresets.message_title)
                .where(EmailsPresets.id == preset_id)
            )
            _subject = _data.scalars().one()

            _data = session.execute(
                select(EmailsPresets.message_text)
                .where(EmailsPresets.id == preset_id)
            )
            _text = _data.scalars().one()

        except sqlalchemy.exc.NoResultFound:
            return OperationStates.emails_preset_not_exists

        try:
            _data = session.execute(
                select(Emails.email)
                .join(EmailsList)
                .where(EmailsList.preset_id == preset_id)
            )
            _emails = _data.scalars().all()
        except sqlalchemy.exc.NoResultFound:
            return OperationStates.emails_preset_emails_not_exists

        try:
            _data = session.execute(
                select(EmailsSMTP.email)
                .where(EmailsSMTP.user_id == _user_id)
            )
            _sender = _data.scalars().one()

            _data = session.execute(
                select(EmailsSMTP.password)
                .where(EmailsSMTP.user_id == _user_id)
            )
            _password = _data.scalars().one()
        except sqlalchemy.exc.NoResultFound:
            return OperationStates.emails_smtp_not_exists

    mail_params = {'TLS': True, 'host': 'smtp.gmail.com', 'password': _password,
                   'user': _sender, 'port': 587}

    # Prepare Message
    msg = MIMEMultipart()
    msg.preamble = _subject
    msg['Subject'] = _subject
    msg['From'] = _sender

    msg.attach(MIMEText(_text, text_type, 'utf-8'))
    for f in files or []:
        with open(Path(f'./trashbox/{_user_id}/audios/' + f), "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    # Contact SMTP server and send Message
    host = mail_params.get('host', 'localhost')
    is_ssl = mail_params.get('SSL', False)
    is_tls = mail_params.get('TLS', False)
    if is_ssl and is_tls:
        raise ValueError('SSL and TLS cannot both be True')
    port = mail_params.get('port', 465 if is_ssl else 25)
    # For aiosmtplib 3.0.1 we must set argument start_tls=False
    # because we will explicitly be calling starttls ourselves when
    # isTLS is True:
    smtp = aiosmtplib.SMTP(hostname=host, port=port, start_tls=False, use_tls=is_ssl)
    await smtp.connect()
    if is_tls:
        await smtp.starttls()
    if 'user' in mail_params:
        await smtp.login(mail_params['user'], mail_params['password'])
    for email in _emails:
        msg['To'] = email
        await smtp.send_message(msg)
        await smtp.quit()


async def main():
    email_address = 'reker.bf@gmail.com'
    co1 = send_mail_async(email_address,
                          ['farosskill@bk.ru'],
                          'Test 1',
                          'Test 1 Message',
                           text_type='plain'
                           )
    co2 = send_mail_async(email_address,
                          ['reker.bf@bk.ru'],
                         'Test 2',
                         'Test 2 Message',
                          text_type='plain'
                          )
    await asyncio.gather(co1, co2)


if __name__ == '__main__':
    asyncio.run(main())


async def get_current_smtp_settings(ctx: CallbackQuery):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        try:
            _data = session.execute(
                select(EmailsSMTP.email)
                .where(EmailsSMTP.user_id == _user_id)
            )
            _result = _data.scalars().one()
        except sqlalchemy.exc.NoResultFound:
            _result = None

    return _result


async def set_current_smtp_settings(ctx: Message, email: str, password: str):
    _user_id = ctx.from_user.id

    with (Session(engine) as session):
        new_smtp = EmailsSMTP(
            user_id=ctx.from_user.id,
            email=email,
            password=password,
        )
        try:
            session.add(new_smtp)
            session.commit()
        except (psycopg2.errors.UniqueViolation, psycopg2.errors.IntegrityError, sqlalchemy.exc.IntegrityError) as exc:
            logging.info('Update user smtp. Username - %s' % ctx.from_user.username)
            session.reset()
            stmt = select(EmailsSMTP).where(EmailsSMTP.user_id == ctx.from_user.id)
            smtp = session.scalars(stmt).one()
            smtp.email = email
            smtp.password = password
            session.commit()

        return OperationStates.emails_smtp_added


async def get_emails_list(ctx: CallbackQuery):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        _emails = session.execute(
            select(Emails.email)
            .join(EmailsMatching, Emails.id == EmailsMatching.email_id)
            .where(EmailsMatching.user_id == _user_id)
        ).unique().scalars().all()

        _pages_count = math.ceil(len(_emails) / 10)
        _sorted_emails = []
        for _i in range(0, _pages_count):
            if _i == _pages_count:
                _sorted_emails.append(_emails[_i*10+1:])
            else:
                _sorted_emails.append(_emails[_i*10:_i*10+10])
    return _sorted_emails


async def get_emails_presets_list(ctx: CallbackQuery):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        _presets = session.execute(
            select(EmailsPresets.id, EmailsPresets.name)
            .where(EmailsPresets.user_id == _user_id)
        )
        _result = dict(_presets.tuples().all())

    return _result


async def add_new_preset(ctx: Message):
    preset_name = ctx.text
    with (Session(engine) as session):
        new_preset = EmailsPresets(
            user_id=ctx.from_user.id,
            name=preset_name,
        )
        try:
            check_unique = session.execute(
                select(EmailsPresets.id)
                .where(EmailsPresets.name == preset_name)
                .where(EmailsPresets.user_id == ctx.from_user.id)
            ).scalars().one()
        except sqlalchemy.exc.NoResultFound:
            check_unique = None

        if not check_unique:
            session.add(new_preset)
            session.commit()
            return OperationStates.emails_preset_added
        else:
            logging.info(
                f'Matching email already exists. Username - {ctx.from_user.username}, email - {ctx.text}'
            )
            return OperationStates.emails_preset_exists


def add_target_email_sync(ctx, emails_list: list, session: Session):
    for email in emails_list:
        _email = email.strip()
        mail_ids = list(session.execute(select(Emails.id)).scalars().all())
        try:
            last_email_id = session.execute(select(Emails.id).where(Emails.email == _email)).scalars().one()
        except sqlalchemy.exc.NoResultFound:
            if mail_ids:
                last_email_id = max(mail_ids) + 1
            else:
                last_email_id = 1

        try:
            check_exists = session.execute(
                select(Emails.id)
                .where(Emails.email == _email)
            ).scalars().one()
        except sqlalchemy.exc.NoResultFound:
            check_exists = None

        try:
            if check_exists:
                check_matching_exists = session.execute(
                    select(EmailsMatching.email_id)
                    .where(EmailsMatching.user_id == ctx.from_user.id)
                    .where(EmailsMatching.email_id == last_email_id)
                ).scalars().one()
            else:
                check_matching_exists = None
        except sqlalchemy.exc.NoResultFound:
            check_matching_exists = None

        new_email = Emails(
            email=_email,
        )

        if not check_exists:
            session.add(new_email)
            session.commit()
            last_email_id = session.execute(select(Emails.id).where(Emails.email == _email)).scalars().one()
        else:
            logging.info('Adding matching email. Username - %s' % ctx.from_user.username)
            session.reset()
            last_email_id = check_exists

        new_matching = EmailsMatching(
            user_id=ctx.from_user.id,
            email_id=last_email_id,
        )

        if not check_matching_exists:
            session.add(new_matching)
            session.commit()

        else:
            logging.info(
                f'Matching email already exists. Username - {ctx.from_user.username}, email - {ctx.text}'
            )
            continue


async def add_target_email(ctx: Message):
    emails = ctx.text
    emails_list = emails.split('\n')
    try:
        with Session(engine) as session:
            add_target_email_sync(ctx, emails_list, session)
            await asyncio.sleep(0)

        return OperationStates.email_added
    except Exception as exc:
        logging.info(
            f'Something wrong in added email. Username - {ctx.from_user.username}, email - {ctx.text}'
        )
        return OperationStates.something_wrong


async def get_current_preset_message_title(ctx: CallbackQuery, preset_id: int):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        _presets = session.execute(
            select(EmailsPresets.message_title)
            .where(EmailsPresets.id == preset_id)
        )
        _result = _presets.scalars().one()

    return _result


async def get_current_preset_message_text(ctx: CallbackQuery, preset_id: int):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        _presets = session.execute(
            select(EmailsPresets.message_text)
            .where(EmailsPresets.id == preset_id)
        )
        _result = _presets.scalars().one()

    return _result


async def get_current_preset_emails(ctx: CallbackQuery, preset_id: int):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        _presets = session.execute(
            select(Emails.email)
            .join(EmailsList)
            .where(EmailsList.preset_id == preset_id)
        )
        _result = _presets.scalars().all()
        print(_result)

    return _result


async def add_message_title(ctx: Message, preset_id: int):
    preset_title = ctx.text
    with (Session(engine) as session):
        try:
            stmt = select(EmailsPresets).where(EmailsPresets.id == preset_id)
            user = session.scalars(stmt).one()
            user.message_title = preset_title
            session.commit()
        except Exception as exc:
            logging.info(
                f'Something wrong in alter table. Username - {ctx.from_user.username}', exc_info=exc
            )
            return OperationStates.something_wrong

    return OperationStates.emails_preset_title_added


async def add_message_text(ctx: Message, preset_id: int):
    preset_text = ctx.text
    with (Session(engine) as session):
        try:
            stmt = select(EmailsPresets).where(EmailsPresets.id == preset_id)
            user = session.scalars(stmt).one()
            user.message_text = preset_text
            session.commit()
        except Exception as exc:
            logging.info(
                f'Something wrong in alter table. Username - {ctx.from_user.username}', exc_info=exc
            )
            return OperationStates.something_wrong

    return OperationStates.emails_preset_message_added


async def add_preset_emails(ctx: Message, preset_id: int):
    emails_text = ctx.text
    emails = emails_text.split('\n')
    with Session(engine) as session:
        stmt = select(EmailsList).where(EmailsList.preset_id == preset_id)
        emails_list = session.scalars(stmt).all()
        for eml in emails_list:
            session.delete(eml)
        session.commit()

        for email in emails:
            email = email.strip()
            try:
                _presets = session.execute(
                    select(Emails.id)
                    .where(Emails.email == email)
                )
                _result = _presets.scalars().one()
            except sqlalchemy.exc.NoResultFound:
                ctx_dict = ctx.__dict__
                ctx_dict['text'] = email
                new_ctx = Message(
                    **ctx_dict
                )
                add_target_email_sync(new_ctx, [email], session)

                _presets = session.execute(
                    select(Emails.id)
                    .where(Emails.email == email)
                )
                _result = _presets.scalars().one()

            new_emails_list = EmailsList(
                preset_id=preset_id,
                email_id=int(_result),
            )

            session.add(new_emails_list)
            session.commit()

    return OperationStates.emails_preset_emails_added
