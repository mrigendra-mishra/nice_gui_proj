from typing import Optional
import sqlite3
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from nicegui import Client, app, ui

# in reality users passwords would obviously need to be hashed
passwords = {'user1': 'pass1', 'user2': 'pass2'}

# Setting up SQL connector
sql_connector = sqlite3.connect("ICON-users.db")
# Creating the Cursor for the SQL db
cursor_obj = sql_connector.cursor()

unrestricted_page_routes = {'/login'}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)


@ui.page('/')
def main_page() -> None:
    with ui.column().classes('absolute-center items-center'):
        ui.label(f'Hello {app.storage.user["username"]}!').classes('text-2xl')
        ui.button(on_click=lambda: ui.navigate.to('/subpage'), icon='logout')
        ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout') \
            .props('outline round')


@ui.page('/subpage')
def test_page() -> None:
    with ui.column().classes('absolute-center items-center'):
        ui.label('This is a sub page.')
        ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout') \
            .props('outline round')



@ui.page('/login')
def login() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        my_query = f"""SELECT * FROM user_creds uc WHERE uc.username = '{username.value}' and uc.password = '{password.value}'"""
        cursor_obj.execute(my_query)
        results = cursor_obj.fetchall()
        sql_connector.commit()
        sql_connector.close()
        if len(results) != 0:
            app.storage.user.update({'username': username.value, 'user_uid': results[0][2], 'authenticated': True})
            ui.notify(app.storage.user.get('user_uid'), color='negative')
            print(app.storage.user.get('user_uid'))
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
    return None

ui.run(storage_secret='My_nice_gui_@_1312_1993')