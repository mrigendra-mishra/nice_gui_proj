"""
This initializes an app using Nice GUI.

The app leveraging power of LLM for knowledge sharing
"""
# pylint: disable=R0903
from typing import Optional, List, Tuple
import sqlite3
import time
from uuid import uuid4 as uuid
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import google.generativeai as gen_ai
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from nicegui import Client, app, ui

unrestricted_page_routes = {'/login', '/signup'}
messages: List[Tuple[str, str, str, str]] = []
OPENAI_API_KEY = 'set'
GOOGLE_API_KEY = 'AIzaSyCTau5yZsRdCGO8UtjD3bl00IDvR6j6z8M'
gen_ai.configure(api_key=GOOGLE_API_KEY)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    This middleware restricts access to all NiceGUI pages.

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


@ui.refreshable
def chat_messages(own_id: str) -> None:
    """CHat message definition"""
    for user_id, avatar, text, stamp in messages:
        ui.chat_message(text=text, stamp=stamp, avatar=avatar, sent=own_id == user_id)
    ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')


@ui.page('/')
def main_page() -> None:
    """
    This defines the Homepage of the app
    """
    llm = ChatGoogleGenerativeAI(model="gemini-pro", streaming=True, safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }, temperature=0, google_api_key=GOOGLE_API_KEY)

    ui.page_title('Home | JARVIS')
    ui.label(f'Hello {app.storage.user["first_name"]}!').classes('text-2xl')
    # ui.button(on_click=lambda: ui.navigate.to('/subpage'), icon='logout')
    with ui.card().classes('absolute-right'):
        ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')),
                  icon='logout').props('outline round')

    async def send() -> None:
        question = text.value
        text.value = ''

        with message_container:
            ui.chat_message(text=question, name='You', sent=True)
            response_message = ui.chat_message(name='Bot', sent=False)
            spinner = ui.spinner(type='dots')

        response = ''
        async for chunk in llm.astream(question):
            response += chunk.content
            response_message.clear()
            with response_message:
                ui.html(response)
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        message_container.remove(spinner)

    ui.add_css(r'a:link, a:visited {color: inherit !important;'
               r'text-decoration: none; font-weight: 500}')

    # the queries below are used to expand the contend down to \
    # the footer (content can then use flex-grow to expand)
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    with ui.tabs().classes('w-full') as tabs:
        chat_tab = ui.tab('Chat')
        # logs_tab = ui.tab('Logs')
    with ui.tab_panels(
            tabs,
            value=chat_tab
    ).classes('w-full max-w-2xl mx-auto flex-grow items-stretch'):
        message_container = ui.tab_panel(chat_tab).classes('items-stretch')
        # with ui.tab_panel(logs_tab):
        #     log = ui.log().classes('w-full h-full')

    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            placeholder = 'message' if OPENAI_API_KEY != 'not-set' else \
                'Please provide your OPENAI key in the Python script first!'
            text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', send)
        ui.markdown('Pwered by [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary')


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
                            validation={
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
        my_query = f"""SELECT first_name, last_name, username,
                              password, user_uid
                    FROM user_creds uc
                    WHERE uc.username = '{username.value}' and
                    uc.password = '{password.value}'"""
        cursor_obj.execute(my_query)
        results = cursor_obj.fetchall()
        sql_connector.commit()
        sql_connector.close()
        if len(results) != 0:
            app.storage.user.update({
                'username': username.value,
                'first_name': results[0][0],
                'last_name': results[0][1],
                'user_uid': results[0][4],
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
