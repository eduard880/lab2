from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Настройка драйвера с явными ожиданиями
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 10)  # Ожидание до 10 секунд


def print_step(message):
    print(f"• {message}")


def test_authorization():
    try:
        print("\n[Проверка авторизации]")

        # Открытие страницы авторизации
        driver.get("http://127.0.0.1:8000/login/")
        print_step("Открыта страница авторизации")

        # Ввод данных
        username = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
        username.send_keys("eduard1")

        password = driver.find_element(By.ID, "id_password")
        password.send_keys("edik2005")
        print_step("Данные для ввода введены")

        # Нажатие кнопки входа
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        print_step("Форма авторизации отправлена")

        # Проверка успешной авторизации
        wait.until(EC.title_contains("Список книг"))
        print_step("Авторизация прошла успешно")

        return True

    except Exception as e:
        print(f"❌ Ошибка авторизации: {str(e)}")
        driver.save_screenshot("auth_error.png")
        return False


def test_order_processing():
    try:
        print("\n[Проверка заказа]")

        if not test_authorization():
            raise Exception("Не удалось авторизоваться")

        # Открытие страницы с книгами
        driver.get("http://127.0.0.1:8000/books/")

        # Добавление книги в корзину
        add_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "В корзину")]'))
        )
        book_title = driver.find_element(
            By.XPATH,
            '//li[.//button[contains(text(), "В корзину")]]//h3'
        ).text
        print_step(f"Добавляем книгу: {book_title}")
        add_button.click()

        # Переход в корзину
        cart_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Корзина")]'))
        )
        cart_button.click()

        # Оформление заказа
        order_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Оформить заказ")]'))
        )
        order_button.click()
        print_step("Заказ успешно оформлен")

        # Проверка информации о заказе
        order_info = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="order-info"]'))
        )
        print_step(f"Информация о заказе: {order_info.text[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Ошибка при оформлении заказа: {str(e)}")
        driver.save_screenshot("order_error.png")
        return False


def main():
    try:
        # Запуск тестов
        auth_result = test_authorization()
        order_result = test_order_processing() if auth_result else False

        # Вывод итогов
        print("\n=== Результаты тестирования ===")
        print(f"Авторизация: {'✅ Успешно' if auth_result else '❌ Ошибка'}")
        print(f"Оформление заказа: {'✅ Успешно' if order_result else '❌ Ошибка'}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()