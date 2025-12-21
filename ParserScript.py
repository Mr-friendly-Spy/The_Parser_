import re
import urllib.request
import csv
from html import unescape


def fetch_website_content(url):
    """Загружает содержимое веб-страницы"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return None


def extract_organizations(html_content):
    """Извлекает данные об организациях из HTML"""
    organizations = []

    # Находим все блоки с организациями
    # Каждая организация находится в блоке <div class="org-widget">
    org_blocks = re.findall(r'<div class="org-widget\s*"[^>]*>.*?<div class="org-widget__in">.*?</div>\s*</div>',
                            html_content, re.DOTALL)

    print(f"Найдено блоков с организациями: {len(org_blocks)}")

    for block in org_blocks:
        org_data = {}

        # Извлекаем название организации
        name_match = re.search(r'<a[^>]*class="org-widget-header__title-link"[^>]*>([^<]+)</a>', block)
        if name_match:
            org_data['name'] = unescape(name_match.group(1).strip())
        else:
            org_data['name'] = 'Нет названия'

        # Извлекаем адрес
        address_match = re.search(
            r'<span[^>]*class="org-widget-header__meta org-widget-header__meta--location"[^>]*>([^<]+)</span>', block)
        if address_match:
            org_data['address'] = unescape(address_match.group(1).strip())
        else:
            org_data['address'] = 'Нет адреса'

        # Извлекаем телефоны
        phones = []
        # Ищем все блоки спецификаций
        spec_blocks = re.findall(r'<dl class="spec">.*?</dl>', block, re.DOTALL)

        for spec_block in spec_blocks:
            # Проверяем, есть ли в блоке "Телефон"
            if 'Телефон' in spec_block:
                # Извлекаем значение телефона
                phone_value = re.search(r'<dd class="spec__value">([^<]+)</dd>', spec_block)
                if phone_value:
                    phones_text = phone_value.group(1).strip()
                    # Разделяем телефоны по запятым
                    phone_list = [phone.strip() for phone in phones_text.split(',') if phone.strip()]
                    phones.extend(phone_list)

        org_data['phones'] = ', '.join(phones) if phones else 'Нет телефона'

        # Извлекаем часы работы
        hours = 'Нет информации'
        for spec_block in spec_blocks:
            if 'Часы работы' in spec_block:
                hours_value = re.search(r'<dd class="spec__value">([^<]+)</dd>', spec_block)
                if hours_value:
                    hours = unescape(hours_value.group(1).strip())
                    break

        org_data['hours'] = hours

        # Извлекаем отзывы/рейтинг
        reviews_text = 'Нет отзывов'
        reviews_count = '0'

        # Ищем блок с отзывами
        feedback_match = re.search(r'<span class="org-widget-feedback__rate-count">\s*([^<]+)\s*</span>', block)
        if feedback_match:
            reviews_count = feedback_match.group(1).strip()
            reviews_text = reviews_count

        # Ищем текст отзыва
        comment_match = re.search(r'<div class="org-widget-feedback__comment">.*?<p>\s*(.*?)\s*</p>', block, re.DOTALL)
        if comment_match:
            comment = unescape(comment_match.group(1).strip())
            # Ограничиваем длину комментария
            if len(comment) > 100:
                comment = comment[:100] + '...'
            reviews_text = f"{reviews_count} | {comment}"

        org_data['reviews'] = reviews_text

        # Извлекаем дополнительные услуги (если есть)
        services = []
        services_match = re.search(r'<span class="org-widget-header__meta">(.*?)</span>', block)
        if services_match and 'org-widget-header__meta--location' not in services_match.group(0):
            services_text = services_match.group(1).strip()
            # Убираем лишние пробелы и переносы строк
            services_text = re.sub(r'\s+', ' ', services_text)
            services = [s.strip() for s in services_text.split(',') if s.strip()]

        org_data['services'] = ', '.join(services) if services else 'Нет информации'

        organizations.append(org_data)

    return organizations


def save_to_csv(data, filename='avtoservisy.csv'):
    """Сохраняет данные в CSV-файл"""
    if not data:
        print("Нет данных для сохранения")
        return

    # Определяем заголовки столбцов
    fieldnames = ['Название организации', 'Адрес', 'Телефоны', 'Часы работы', 'Отзывы/Рейтинг', 'Услуги']

    try:
        with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Записываем заголовки
            writer.writeheader()

            # Записываем данные
            for org in data:
                writer.writerow({
                    'Название организации': org['name'],
                    'Адрес': org['address'],
                    'Телефоны': org['phones'],
                    'Часы работы': org['hours'],
                    'Отзывы/Рейтинг': org['reviews'],
                    'Услуги': org['services']
                })

        print(f"Данные успешно сохранены в файл: {filename}")
        print(f"Количество записей: {len(data)}")

    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")


def main():
    """Основная функция"""
    url = "https://msk.spravker.ru/avtoservisy-avtotehcentry"

    print(f"Загружаем данные с {url}")
    print("Это может занять несколько секунд...")

    # Загружаем содержимое страницы
    html_content = fetch_website_content(url)

    if html_content:
        print("Содержимое страницы успешно загружено")
        print("Извлекаем данные об организациях...")

        # Извлекаем данные
        organizations = extract_organizations(html_content)

        if organizations:
            print(f"Найдено {len(organizations)} организаций")

            # Показываем первые 5 организаций для проверки
            print("\nПример извлеченных данных (первые 5 записей):")
            print("=" * 100)
            for i, org in enumerate(organizations[:5], 1):
                print(f"\n{i}. {org['name']}")
                print(f"   Адрес: {org['address']}")
                print(f"   Телефоны: {org['phones']}")
                print(f"   Часы работы: {org['hours']}")
                print(f"   Отзывы: {org['reviews']}")
                print(f"   Услуги: {org['services']}")
            print("=" * 100)

            # Сохраняем в CSV
            save_to_csv(organizations)

            # Для отладки: можно посмотреть все названия организаций
            print("\nСписок всех найденных организаций:")
            for i, org in enumerate(organizations, 1):
                print(f"{i:3}. {org['name']}")

        else:
            print("Не удалось извлечь данные об организациях")
            # Для отладки: посмотрим, что есть в HTML
            print("Проверяем наличие организаций в HTML...")
            if 'org-widget' in html_content:
                print("Найдены блоки с классом 'org-widget'")
                # Попробуем найти хотя бы одну организацию по другому паттерну
                org_titles = re.findall(r'class="org-widget-header__title-link"[^>]*>([^<]+)</a>', html_content)
                print(f"Найдено названий организаций: {len(org_titles)}")
                if org_titles:
                    print("Первые 5 названий:")
                    for title in org_titles[:5]:
                        print(f"  - {unescape(title)}")
    else:
        print("Не удалось загрузить страницу")


if __name__ == "__main__":
    main()