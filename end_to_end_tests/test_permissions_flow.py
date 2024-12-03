import time

from selenium.webdriver.common.by import By

from .conftest import register_user, login_user, wait_for_element, assert_url, delete_user
from .const import MAIN_PAGE, LOGIN_PAGE, PROFILE_PAGE


def test_permissions_flow_basics(driver, user_data, post_data):
    driver.get(MAIN_PAGE)

    create_post_button = wait_for_element(driver, By.CLASS_NAME, "_button_1u3qt_53")
    create_post_button.click()

    assert_url(driver=driver, expected_url=LOGIN_PAGE)

    link_to_register = wait_for_element(driver, By.CSS_SELECTOR, "a[href*='/register']")
    link_to_register.click()

    register_user(driver, user_data)

    assert_url(driver=driver, expected_url=LOGIN_PAGE)

    login_user(driver, user_data)

    assert_url(driver=driver, expected_url=PROFILE_PAGE)

    driver.get(MAIN_PAGE)

    create_post_button = wait_for_element(driver, By.CLASS_NAME, "_button_1u3qt_53")
    create_post_button.click()

    topic = wait_for_element(driver, By.CLASS_NAME, "_textarea_7b4hy_47")
    topic.send_keys(post_data.get("topic"))

    description = wait_for_element(driver, By.CLASS_NAME, "_textarea_7b4hy_47._description_7b4hy_75")
    description.send_keys(post_data.get("description"))

    tags = wait_for_element(driver, By.CLASS_NAME, "_tags_7b4hy_85")
    tags.send_keys(post_data.get("tags"))

    submit = wait_for_element(driver, By.CLASS_NAME, "_button_7b4hy_99")
    submit.click()

    delete_user(driver, user_data)
