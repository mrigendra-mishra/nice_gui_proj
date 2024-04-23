"""
This initalizes an app using Nice GUI.

The app leveraging power of LLM for knowledge sharing
"""
# pylint: disable=R0903
from typing import Optional
import sqlite3
import time
from uuid import uuid4 as uuid
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import Client, app, ui



unrestricted_page_routes = {'/login', '/signup'}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if (request.url.path in Client.page_routes.values() and request.url.path
                    not in unrestricted_page_routes):
                # remember where the user wanted to go
                app.storage.user['referrer_path'] = request.url.path
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)


@ui.page('/')
def main_page() -> None:
    """
    This defines the Homepage of the app
    """
    with ui.column().classes('absolute-center items-center'):
        ui.label(f'Hello {app.storage.user["username"]}!').classes('text-2xl')
        ui.button(on_click=lambda: ui.navigate.to('/subpage'), icon='logout')
        ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')),
                  icon='logout').props('outline round')


@ui.page('/subpage')
def test_page() -> None:
    """
    This is a test page
    """
    with ui.column().classes('absolute-center items-center'):
        ui.label('This is a sub page.')
        ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')),
                  icon='logout').props('outline round')


@ui.page('/signup')
def signup() -> Optional[RedirectResponse]:
    """
    This page is for new signups
    """
    def try_signup():
        user_uid = str(uuid())
        # Setting up SQL connector
        sql_connector = sqlite3.connect("nice_gui_db.db")
        # Creating the Cursor for the SQL db
        cursor_obj = sql_connector.cursor()
        my_query = f"""INSERT INTO user_creds (first_name, last_name, username, password, user_uid)
                    VALUES ('{first_name.value}','{last_name.value}','{username.value}',
                    '{password.value}','{user_uid}')"""
        cursor_obj.execute(my_query)
        sql_connector.commit()
        sql_connector.close()
        ui.notify('Welcome!!', color='negative')
        time.sleep(5)
        ui.navigate.to('/login')

    ui.page_title('Sign-Up | JARVIS')
    with ui.card().classes('absolute-center'):
        first_name = ui.input('First Name',
                              validation={
                                  'Not a valid name': lambda value: value.isalpha()
                              })
        last_name = ui.input('Last Name',
                             validation={
                                 'Not a valid name': lambda value: value.isalpha()
                             })
        username = ui.input('Username').on('keydown.enter', try_signup)
        password = ui.input('Password', password=True,
                            password_toggle_button=True,
                            validation= {
                                'Too short': lambda value: len(value) >= 6
                            }
                            ).on('keydown.enter', try_signup)
        ui.button('Sign Up', on_click=try_signup)
        ui.button('Login', on_click=lambda: ui.navigate.to('/login'))


@ui.page('/login')
def login() -> Optional[RedirectResponse]:
    """
    This page is for logging in to the application. This is an unrestricted page.
    """
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        # Setting up SQL connector
        sql_connector = sqlite3.connect("nice_gui_db.db")
        # Creating the Cursor for the SQL db
        cursor_obj = sql_connector.cursor()
        my_query = f"""SELECT * FROM user_creds uc
                    WHERE uc.username = '{username.value}' and 
                    uc.password = '{password.value}'"""
        cursor_obj.execute(my_query)
        results = cursor_obj.fetchall()
        sql_connector.commit()
        sql_connector.close()
        if len(results) != 0:
            app.storage.user.update({
                'username': username.value,
                'user_uid': results[0][2],
                'authenticated': True
            })
            ui.notify(app.storage.user.get('user_uid'), color='negative')
            print(app.storage.user.get('user_uid'))
            # go back to where the user wanted to go
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    ui.page_title('Login | JARVIS')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True,
                            password_toggle_button=True).on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
        # ui.button('Sign up', on_click=goto_signup)
        ui.button('Sign up', on_click=lambda: ui.navigate.to('/signup'))
    return None


ui.run(storage_secret='My_nice_gui_@_1312_1993')
