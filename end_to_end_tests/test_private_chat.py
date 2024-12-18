import time

from selenium.webdriver.common.by import By

from .conftest import (
    register_user,
    assert_url,
    login_user,
    wait_for_element,
    fill_input,
    delete_user,
)
from .const import MAIN_PAGE, LOGIN_PAGE, PROFILE_PAGE, REGISTER_PAGE


def test_private_chat_flow(driver, user_data, user2_data):
    driver.get(MAIN_PAGE)

    link_to_register = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/register']")
    link_to_register.click()

    assert_url(driver=driver, expected_url=REGISTER_PAGE)

    # Register the user
    register_user(driver, user_data)

    assert_url(driver=driver, expected_url=LOGIN_PAGE)

    link_to_register = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/register']")
    link_to_register.click()

    assert_url(driver=driver, expected_url=REGISTER_PAGE)

    register_user(driver, user2_data)

    assert_url(driver=driver, expected_url=LOGIN_PAGE)

    # Log in the user
    login_user(driver, user_data)

    assert_url(driver=driver, expected_url=PROFILE_PAGE)

    fill_input(driver=driver, placeholder="Type here to search...", value="@testuser2")

    time.sleep(3)

    admin_account = wait_for_element(
        driver, By.CSS_SELECTOR, "a[class='_wrapper_yc7q6_1'"
    )
    admin_account.click()

    go_to_chat = wait_for_element(driver, By.CLASS_NAME, "_button_1fp5i_57")
    go_to_chat.click()

    test_message = "Hello WebSocket!"

    message = wait_for_element(driver, By.CLASS_NAME, "_input_1e24m_75")
    message.send_keys(test_message)

    send_message = wait_for_element(driver, By.CLASS_NAME, "_button_1e24m_95")
    send_message.click()

    received_message = wait_for_element(driver, By.CLASS_NAME, f"_message_3uy5w_1")

    assert received_message, "No WebSocket handshake found."

    delete_user(driver, user_data)

    driver.get(MAIN_PAGE)

    link_to_register = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/register']")
    link_to_register.click()

    link_to_login = wait_for_element(driver, By.CLASS_NAME, "_link_13869_69")
    link_to_login.click()

    login_user(driver, user2_data)

    time.sleep(5)

    delete_user(driver, user2_data)

    time.sleep(5)
