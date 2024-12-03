import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
# from sqlalchemy.ext.asyncio import create_async_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.future import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from .const import DATABASE_URL
# from db import models
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

from end_to_end_tests.const import MAIN_PAGE


@pytest.fixture(scope="module")
def driver():
    # Setting up Firefox options
    options = Options()
    options.headless = True  # Optional: run in headless mode
    options.set_preference("network.cookie.sameSite.laxByDefault", False)  # Allow SameSite=None by default
    options.set_preference("network.cookie.sameSite.noneRequiresSecure",False)  # Don't require "Secure" for SameSite=None cookies
    options.set_preference("dom.ipc.processCount", 1)  # Optimize performance in Docker (important for headless mode)
    options.set_preference("privacy.cookieBehavior", 0)

    # Connect to Selenium server running in Docker container
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',  # Selenium server URL
        options=options,
        keep_alive=True,  # Optional: keep the connection alive for the session
    )

    yield driver

    driver.quit()

#
# @pytest.fixture(scope="module")
# async def async_session(user_data):
#     engine = create_async_engine(DATABASE_URL, echo=True, future=True)
#     async_session_factory = sessionmaker(
#         bind=engine,
#         class_=AsyncSession,
#         expire_on_commit=False,
#     )
#
#     async with async_session_factory() as session:
#         await add_second_user_for_testing(db=session)
#         yield session
#         await remove_user_by_username(db=session, usernames=(user_data.get("username"), "testuser2"))
#


@pytest.fixture(scope="module")
def user_data():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture(scope="module")
def user2_data():
    return {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture(scope="module")
def post_data():
    return {
        "topic": "test_topic",
        "description": "test_description",
        "tags": "test_tag"
    }

#
# async def remove_user_by_username(db: AsyncSession, usernames: tuple) -> None:
#     query = await db.execute(select(models.DBUser).filter(models.DBUser.username.in_(usernames)))
#     users = query.scalars().all()
#     if users:
#         for user in users:
#             await db.delete(user)
#         await db.commit()
#         print(f"{len(users)} user(s) with username {usernames} have been removed.")
#     else:
#         print(f"No user found with username {usernames}.")
#
#
# async def add_second_user_for_testing(db: AsyncSession) -> None:
#     second_user = models.DBUser(
#         email="testuser2@example.com",
#         username="testuser2",
#         password="TestPassword123!"
#     )
#     db.add(second_user)
#     await db.commit()
#     await db.refresh(second_user)


def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def fill_input(driver, placeholder, value):
    input_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"input[placeholder='{placeholder}']")
        )
    )
    input_field.clear()
    input_field.send_keys(value)


def assert_url(driver, expected_url):
    WebDriverWait(driver, 10).until(EC.url_to_be(expected_url))
    assert driver.current_url == expected_url


def register_user(driver, user_data):
    # Fill out the registration form
    fill_input(driver, "User name", user_data["username"])
    fill_input(driver, "Email", user_data["email"])
    fill_input(driver, "Password", user_data["password"])
    fill_input(driver, "Password again", user_data["password"])

    # Submit the registration form
    submit = wait_for_element(driver, By.CLASS_NAME, "_button_13869_55")
    submit.click()


def login_user(driver, user_data):
    fill_input(driver, "Email", user_data["email"])
    fill_input(driver, "Password", user_data["password"])

    submit = wait_for_element(driver, By.CLASS_NAME, "_button_f50vs_57")
    submit.click()


def delete_user(driver, user_data):
    pop_up_button = wait_for_element(driver, By.CLASS_NAME, "_profile__pop_up_button_16yyf_297")
    pop_up_button.click()

    settings = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/settings']")
    settings.click()

    delete_button = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/delete-account']")
    delete_button.click()

    input_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"input[type='password']")
        )
    )
    input_field.clear()
    input_field.send_keys(user_data.get("password"))

    pop_up_button = wait_for_element(driver, By.CLASS_NAME, "_profile__pop_up_button_16yyf_297")
    pop_up_button.click()

    confirm_button = wait_for_element(driver, By.CLASS_NAME, "_button_1b9u1_51")
    confirm_button.click()

    again_confirm_button = wait_for_element(driver, By.CLASS_NAME, "_confirm_17jzi_85")
    again_confirm_button.click()

