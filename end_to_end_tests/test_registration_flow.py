import time

from selenium.webdriver.common.by import By

from .conftest import register_user, assert_url, login_user, wait_for_element, delete_user
from .const import MAIN_PAGE, LOGIN_PAGE, PROFILE_PAGE, REGISTER_PAGE


def test_registration_login_flow(driver, user_data):
    driver.get(MAIN_PAGE)

    link_to_register = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/register']")
    link_to_register.click()

    assert_url(driver=driver, expected_url=REGISTER_PAGE)

    # Register the user
    register_user(driver, user_data)
    assert_url(driver=driver, expected_url=LOGIN_PAGE)

    # Log in the user
    login_user(driver, user_data)
    assert_url(driver=driver, expected_url=PROFILE_PAGE)

    delete_user(driver, user_data)
