import hashlib
import datetime
import configuration

from .User import User, UserWebQuery
from .user_report import UserReport
from .user_suspend import UserSuspend
from database.database_connection import database_engine as db
from kelp_modules import kelp_module_repo
from kelp_plugins import kelp_plugin_repo

from utils import sql_utils


def get_user_query_object(user: str) -> UserWebQuery:
    if User.query.filter_by(username=user) is not None:
        return UserWebQuery(User.query.filter_by(username=user).first())
    return UserWebQuery(None)


def get_all_user_query_object() -> list:
    li = list()
    for user in get_all_users():
        li.append(get_user_query_object(user))
    return li


def create_user(username, password, email, description, avatar, admin=False):
    password_b = bytes(password, "utf-8")
    pwd_hash = hashlib.sha512(password_b).hexdigest()

    user = User(username, pwd_hash, email, description, avatar, admin=admin)

    if User.query.filter_by(username=user.username).first() is None:
        if User.query.filter_by(email=email).first() is not None:
            return "User with this email already exists"
        db.session.add(user)
        db.session.commit()
        return True

    return "User already exists"


def create_user_report(username, creator, description, report_type):
    if report_type not in configuration.user_report_types:
        return Exception(f"Unknown type: {report_type}")
    report = UserReport(username, creator, description, report_type)
    sql_utils.append_to_db(report, auto_commit=True)


def check_verified(user):
    return User.query.filter_by(username=user).first().activated


def verify_user(code):
    user = User.query.filter_by(activation_code=code).first()
    if user is not None and not user.activated:
        user.activated = True
        sql_utils.commit_db()
        return True
    return False


def delete_user(username):
    user = User.query.filter_by(username=username).first()
    sql_utils.delete_from_db(user)

    remove_reports_by_username(username, False)
    remove_reports_by_creator(username, False)

    kelp_module_repo.remove_user_content(username, False)
    kelp_plugin_repo.remove_user_content(username, False)

    sql_utils.commit_db()

    return True


def remove_reports_by_username(username, auto_commit=True):
    UserReport.query.filter_by(username=username).delete()
    if auto_commit:
        sql_utils.commit_db()


def remove_reports_by_creator(creator, auto_commit=True):
    UserReport.query.filter_by(creator=creator)
    if auto_commit:
        sql_utils.commit_db()


def remove_report_by_id(report_id, auto_commit=True):
    UserReport.query.filter_by(id=report_id).delete()
    if auto_commit:
        sql_utils.commit_db()


def change_username(name, new_name):
    if User.query.filter_by(username=new_name).first() is None:
        user = User.query.filter_by(username=name).first()
        user.username = new_name
        db.session.commit()
        return True
    return False


def change_description(user, description):
    User.query.filter_by(username=user).first().description = description
    sql_utils.commit_db()


def change_email(user, email):
    User.query.filter_by(username=user).first().email = email
    sql_utils.commit_db()


def change_avatar(user, avatar):
    User.query.filter_by(username=user).first().avatar = avatar.stream.read()
    sql_utils.commit_db()


def change_password(user, old, new):
    name = User.query.filter_by(username=user).first()
    if check_user_password(user, old):
        name.password = hashlib.sha512(bytes(new, "utf-8")).hexdigest()
        db.session.commit()
        return True
    return False


def set_password(user, password):
    name = User.query.filter_by(username=user).first()
    name.password = hashlib.sha512(bytes(password, "utf-8")).hexdigest()
    db.session.commit()
    return True


def get_all_reports(add_user_objects=False):
    reports = sql_utils.sql_list_to_json(
        UserReport.query.order_by(UserReport.username.asc()).all()
    )
    if add_user_objects:
        for report in reports:
            report["user"] = get_user_query_object(report["username"])
    return reports


def get_password_hash(user):
    return User.query.filter_by(username=user).first().password


def get_all_users():
    li = []
    for x in User.query.all():
        li.append(x.username)
    return li


def search_users_by_username(search):
    return sql_utils.sql_list_to_json(
        User.query.filter(User.username.ilike(f"%{search}%")).all()
    )


def user_exists(username):
    return User.query.filter_by(username=username).first() is not None


def check_user_password(user, passwd):
    try:
        passwd = hashlib.sha512(bytes(passwd, "utf-8")).hexdigest()
        userdata = User.query.filter_by(username=user).first()
        if user is not None and userdata.password == passwd:
            return True
        return False
    except AttributeError:
        return False


def check_user_passwordhash(user, pwd_hash):
    try:
        userdata = User.query.filter_by(username=user).first()
        if user is not None and userdata.password == pwd_hash:
            return True
        return False
    except AttributeError:
        return False


def get_user_report_by_id(report_id, add_user_object=True):
    obj = sql_utils.sql_to_json(
        UserReport.query.filter_by(id=int(report_id)).first()
    )
    if add_user_object:
        obj["user"] = sql_utils.sql_to_json(
            get_user_query_object(obj["username"])
        )
    return obj


def switch_admin(user):
    val = User.query.filter_by(username=user).first()
    val.admin = not val.admin
    sql_utils.commit_db()


def suspend_user(user, until, message):
    if int(until) > 0:
        until_fin = datetime.datetime.fromtimestamp(float(until)/1000)
    else:
        until_fin = int(until)
    ban = UserSuspend(user, until_fin, message)
    db.session.add(ban)
    db.session.commit()
    return True


def del_suspend_user(user):
    ban = UserSuspend.query.filter_by(username=user).first()
    db.session.delete(ban)
    db.session.commit()
    return True
