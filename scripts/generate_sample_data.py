"""
Script to generate sample Russian vacancies, candidates, and CVs.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from app.models import Position, Candidate
from app.agent_tools import AgentTools
from sqlalchemy.orm import Session
import asyncio
import os

# Sample Russian job descriptions
VACANCIES = [
    """Ищем Senior Python разработчика с опытом работы 5+ лет.

ОБЯЗАТЕЛЬНО:
- Опыт разработки на Python 5+ лет
- Опыт работы с FastAPI или Django
- Знание SQL баз данных (PostgreSQL предпочтительно)
- Опыт работы с Git

ЖЕЛАТЕЛЬНО:
- Опыт с Docker и Kubernetes
- Знание фреймворков машинного обучения
- Опыт работы с облачными платформами (AWS, Azure, GCP)

БОНУС:
- Участие в open source проектах
- Опыт работы с микросервисной архитектурой""",

    """Требуется Frontend разработчик React.

ОБЯЗАТЕЛЬНО:
- Опыт разработки на React 3+ года
- Знание TypeScript
- Опыт работы с Redux или Zustand
- Знание HTML/CSS/JavaScript

ЖЕЛАТЕЛЬНО:
- Опыт с Next.js
- Знание Tailwind CSS
- Опыт работы с GraphQL

БОНУС:
- Опыт с мобильной разработкой (React Native)""",

    """Ищем DevOps инженера.

ОБЯЗАТЕЛЬНО:
- Опыт работы с Kubernetes 2+ года
- Знание Docker
- Опыт настройки CI/CD (GitLab CI, GitHub Actions)
- Знание Linux системного администрирования

ЖЕЛАТЕЛЬНО:
- Опыт с Terraform или Ansible
- Знание облачных платформ (AWS, GCP)
- Опыт с мониторингом (Prometheus, Grafana)

БОНУС:
- Сертификаты облачных провайдеров""",

    """Требуется Data Scientist.

ОБЯЗАТЕЛЬНО:
- Опыт работы с Python 3+ года
- Знание библиотек машинного обучения (scikit-learn, pandas, numpy)
- Опыт работы с SQL
- Знание статистики и математики

ЖЕЛАТЕЛЬНО:
- Опыт с глубоким обучением (TensorFlow, PyTorch)
- Опыт работы с большими данными (Spark, Hadoop)
- Знание визуализации данных

БОНУС:
- Публикации в научных журналах""",

    """Ищем Backend разработчика Java.

ОБЯЗАТЕЛЬНО:
- Опыт разработки на Java 4+ года
- Знание Spring Framework
- Опыт работы с базами данных (PostgreSQL, MySQL)
- Знание REST API

ЖЕЛАТЕЛЬНО:
- Опыт с микросервисной архитектурой
- Знание Kafka или RabbitMQ
- Опыт с Docker и Kubernetes

БОНУС:
- Опыт с Kotlin""",

    """Требуется Fullstack разработчик.

ОБЯЗАТЕЛЬНО:
- Опыт разработки на Python или Node.js 3+ года
- Опыт работы с React или Vue.js
- Знание баз данных (SQL и NoSQL)
- Опыт работы с REST API

ЖЕЛАТЕЛЬНО:
- Опыт с TypeScript
- Знание Docker
- Опыт с облачными платформами

БОНУС:
- Опыт с GraphQL""",

    """Ищем QA инженера (автоматизация).

ОБЯЗАТЕЛЬНО:
- Опыт автоматизации тестирования 2+ года
- Знание Python или Java
- Опыт работы с Selenium или Playwright
- Знание методологий тестирования

ЖЕЛАТЕЛЬНО:
- Опыт с API тестированием
- Знание CI/CD
- Опыт с нагрузочным тестированием

БОНУС:
- Сертификаты по тестированию""",

    """Требуется Mobile разработчик (iOS/Android).

ОБЯЗАТЕЛЬНО:
- Опыт разработки мобильных приложений 3+ года
- Знание Swift (iOS) или Kotlin (Android)
- Опыт работы с нативными фреймворками
- Знание архитектурных паттернов (MVVM, MVP)

ЖЕЛАТЕЛЬНО:
- Опыт с React Native или Flutter
- Знание REST API
- Опыт публикации приложений в сторы

БОНУС:
- Опыт с обеими платформами""",

    """Ищем Product Manager.

ОБЯЗАТЕЛЬНО:
- Опыт работы Product Manager 3+ года
- Опыт работы с Agile/Scrum
- Навыки аналитики и работы с данными
- Опыт взаимодействия с разработчиками и дизайнерами

ЖЕЛАТЕЛЬНО:
- Техническое образование
- Опыт работы в IT компании
- Знание инструментов аналитики (Amplitude, Mixpanel)

БОНУС:
- MBA или сертификаты по продукт-менеджменту""",

    """Требуется UX/UI дизайнер.

ОБЯЗАТЕЛЬНО:
- Опыт дизайна интерфейсов 3+ года
- Знание Figma или Sketch
- Портфолио с примерами работ
- Понимание принципов UX

ЖЕЛАТЕЛЬНО:
- Опыт работы с дизайн-системами
- Знание основ фронтенд разработки
- Опыт проведения пользовательских исследований

БОНУС:
- Опыт с анимацией и прототипированием""",

    """Ищем Security Engineer.

ОБЯЗАТЕЛЬНО:
- Опыт работы в информационной безопасности 3+ года
- Знание сетевых протоколов и безопасности
- Опыт проведения аудитов безопасности
- Знание инструментов безопасности

ЖЕЛАТЕЛЬНО:
- Сертификаты (CISSP, CEH)
- Опыт с penetration testing
- Знание compliance требований

БОНУС:
- Опыт работы с bug bounty программами""",

    """Требуется Team Lead разработки.

ОБЯЗАТЕЛЬНО:
- Опыт разработки 5+ лет
- Опыт руководства командой 2+ года
- Знание современных технологий разработки
- Навыки менеджмента и коммуникации

ЖЕЛАТЕЛЬНО:
- Опыт с Agile методологиями
- Знание архитектуры систем
- Опыт найма и онбординга

БОНУС:
- Техническое образование и MBA"""
]

# Sample Russian CVs
CVS = [
    """Иван Петров
Email: ivan.petrov@example.com
Телефон: +7-999-123-45-67
Telegram: @ivan_petrov

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Senior Python разработчик с 7 годами опыта в создании масштабируемых веб-приложений.
Эксперт в FastAPI, Django и PostgreSQL. Сильный опыт работы с микросервисной архитектурой.

ОПЫТ РАБОТЫ:
- Senior Python Developer в TechCorp (2020-настоящее время)
  * Разработка REST API с использованием FastAPI
  * Проектирование и реализация микросервисной архитектуры
  * Работа с Docker и Kubernetes
  * Управление базами данных PostgreSQL

- Python Developer в StartupXYZ (2017-2020)
  * Разработка веб-приложений на Django
  * Внедрение CI/CD пайплайнов
  * Работа с облачными сервисами AWS

ОБРАЗОВАНИЕ:
- Бакалавр компьютерных наук, Университет Технологий (2017)

НАВЫКИ:
Python, FastAPI, Django, PostgreSQL, SQL, Docker, Kubernetes, Git, CI/CD, AWS, Микросервисы""",

    """Мария Сидорова
Email: maria.sidorova@example.com
Телефон: +7-999-234-56-78
WhatsApp: +7-999-234-56-78

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Frontend разработчик с 5 годами опыта в создании современных пользовательских интерфейсов.
Специализация в React, TypeScript и современном CSS.

ОПЫТ РАБОТЫ:
- Frontend Developer в WebStudio (2021-настоящее время)
  * Разработка React приложений с TypeScript
  * Работа с Redux для управления состоянием
  * Оптимизация производительности приложений
  * Работа с REST и GraphQL API

- Junior Frontend Developer в DigitalAgency (2019-2021)
  * Разработка компонентов на React
  * Верстка адаптивных интерфейсов
  * Работа с дизайн-системами

ОБРАЗОВАНИЕ:
- Магистр информационных технологий, МГУ (2019)

НАВЫКИ:
React, TypeScript, JavaScript, HTML, CSS, Redux, Next.js, Tailwind CSS, GraphQL""",

    """Алексей Иванов
Email: alexey.ivanov@example.com
Телефон: +7-999-345-67-89
Telegram: @alexey_devops

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
DevOps инженер с 6 годами опыта в автоматизации инфраструктуры и CI/CD.
Эксперт в Kubernetes, Docker и облачных платформах.

ОПЫТ РАБОТЫ:
- DevOps Engineer в CloudTech (2020-настоящее время)
  * Настройка и управление Kubernetes кластерами
  * Разработка CI/CD пайплайнов на GitLab CI
  * Автоматизация инфраструктуры с Terraform
  * Настройка мониторинга (Prometheus, Grafana)

- System Administrator в HostingPro (2018-2020)
  * Администрирование Linux серверов
  * Настройка Docker контейнеров
  * Работа с базами данных

ОБРАЗОВАНИЕ:
- Бакалавр информационных систем, МГТУ (2018)

НАВЫКИ:
Kubernetes, Docker, Linux, CI/CD, Terraform, Ansible, AWS, GCP, Prometheus, Grafana""",

    """Елена Смирнова
Email: elena.smirnova@example.com
Телефон: +7-999-456-78-90

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Data Scientist с 4 годами опыта в машинном обучении и анализе данных.
Специализация в Python, статистическом анализе и визуализации данных.

ОПЫТ РАБОТЫ:
- Data Scientist в DataAnalytics (2021-настоящее время)
  * Разработка моделей машинного обучения
  * Анализ больших объемов данных
  * Создание дашбордов и визуализаций
  * Работа с SQL и NoSQL базами данных

- Junior Data Analyst в ResearchLab (2019-2021)
  * Анализ данных и создание отчетов
  * Работа с pandas и numpy
  * Статистический анализ

ОБРАЗОВАНИЕ:
- Магистр прикладной математики, МФТИ (2019)

НАВЫКИ:
Python, pandas, numpy, scikit-learn, TensorFlow, SQL, PostgreSQL, MongoDB, Tableau, Jupyter""",

    """Дмитрий Козлов
Email: dmitry.kozlov@example.com
Телефон: +7-999-567-89-01
Telegram: @dmitry_java

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Backend разработчик Java с 6 годами опыта в создании корпоративных приложений.
Эксперт в Spring Framework и микросервисной архитектуре.

ОПЫТ РАБОТЫ:
- Senior Java Developer в EnterpriseSoft (2020-настоящее время)
  * Разработка микросервисов на Spring Boot
  * Работа с Kafka для асинхронной обработки
  * Проектирование REST API
  * Оптимизация производительности приложений

- Java Developer в FinTech (2018-2020)
  * Разработка backend приложений
  * Работа с базами данных PostgreSQL
  * Интеграция с внешними API

ОБРАЗОВАНИЕ:
- Бакалавр программной инженерии, МИФИ (2018)

НАВЫКИ:
Java, Spring Framework, Spring Boot, PostgreSQL, Kafka, RabbitMQ, Docker, Kubernetes, REST API""",

    """Анна Волкова
Email: anna.volkova@example.com
Телефон: +7-999-678-90-12
WhatsApp: +7-999-678-90-12

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Fullstack разработчик с 5 годами опыта в создании веб-приложений.
Опыт работы как с frontend, так и с backend технологиями.

ОПЫТ РАБОТЫ:
- Fullstack Developer в WebSolutions (2021-настоящее время)
  * Разработка fullstack приложений на Node.js и React
  * Проектирование архитектуры приложений
  * Работа с базами данных MongoDB и PostgreSQL
  * Разработка REST и GraphQL API

- Web Developer в StartupHub (2019-2021)
  * Разработка веб-приложений
  * Верстка и frontend разработка
  * Работа с базами данных

ОБРАЗОВАНИЕ:
- Бакалавр информатики, СПбГУ (2019)

НАВЫКИ:
Node.js, React, TypeScript, PostgreSQL, MongoDB, GraphQL, REST API, Docker, AWS""",

    """Сергей Новиков
Email: sergey.novikov@example.com
Телефон: +7-999-789-01-23

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
QA инженер с 4 годами опыта в автоматизации тестирования.
Специализация в Python, Selenium и API тестировании.

ОПЫТ РАБОТЫ:
- QA Automation Engineer в TestPro (2020-настоящее время)
  * Разработка автоматизированных тестов на Python
  * Работа с Selenium и Playwright
  * API тестирование с использованием pytest
  * Настройка CI/CD для тестов

- QA Engineer в SoftwareCorp (2018-2020)
  * Ручное тестирование приложений
  * Написание тест-кейсов
  * Репортинг багов

ОБРАЗОВАНИЕ:
- Бакалавр информационных технологий, МГУ (2018)

НАВЫКИ:
Python, Selenium, Playwright, pytest, API Testing, CI/CD, Git, Jira, TestRail""",

    """Ольга Морозова
Email: olga.morozova@example.com
Телефон: +7-999-890-12-34
Telegram: @olga_mobile

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Mobile разработчик с 5 годами опыта в создании нативных и кроссплатформенных приложений.
Опыт работы с iOS и Android платформами.

ОПЫТ РАБОТЫ:
- Mobile Developer в MobileApps (2020-настоящее время)
  * Разработка iOS приложений на Swift
  * Разработка Android приложений на Kotlin
  * Работа с React Native для кроссплатформенной разработки
  * Публикация приложений в App Store и Google Play

- Junior Mobile Developer в AppStudio (2019-2020)
  * Разработка мобильных приложений
  * Работа с REST API
  * Тестирование приложений

ОБРАЗОВАНИЕ:
- Бакалавр мобильной разработки, МГТУ (2019)

НАВЫКИ:
Swift, Kotlin, React Native, iOS, Android, REST API, Git, Firebase, App Store, Google Play""",

    """Павел Соколов
Email: pavel.sokolov@example.com
Телефон: +7-999-901-23-45

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Product Manager с 6 годами опыта в управлении продуктами и командами разработки.
Опыт работы в IT компаниях с техническими продуктами.

ОПЫТ РАБОТЫ:
- Product Manager в ProductTech (2021-настоящее время)
  * Управление продуктовой стратегией
  * Работа с командами разработки по Agile методологии
  * Анализ метрик и данных продукта
  * Взаимодействие с stakeholders

- Associate Product Manager в StartupInc (2019-2021)
  * Помощь в управлении продуктом
  * Сбор требований от пользователей
  * Анализ конкурентов

ОБРАЗОВАНИЕ:
- MBA, Высшая школа экономики (2019)
- Бакалавр компьютерных наук, МГУ (2017)

НАВЫКИ:
Product Management, Agile, Scrum, Analytics, SQL, Jira, Confluence, Figma, A/B Testing""",

    """Татьяна Лебедева
Email: tatiana.lebedeva@example.com
Телефон: +7-999-012-34-56
Telegram: @tatiana_design

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
UX/UI дизайнер с 5 годами опыта в создании пользовательских интерфейсов.
Специализация в веб и мобильном дизайне.

ОПЫТ РАБОТЫ:
- UX/UI Designer в DesignStudio (2020-настоящее время)
  * Создание дизайна интерфейсов в Figma
  * Проведение пользовательских исследований
  * Работа с дизайн-системами
  * Создание прототипов и анимаций

- Junior Designer в CreativeAgency (2018-2020)
  * Создание графического дизайна
  * Верстка макетов
  * Работа с клиентами

ОБРАЗОВАНИЕ:
- Бакалавр дизайна, МГХПА (2018)

НАВЫКИ:
Figma, Sketch, Adobe XD, Photoshop, Illustrator, User Research, Prototyping, Design Systems""",

    """Михаил Федоров
Email: mikhail.fedorov@example.com
Телефон: +7-999-123-45-67

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Security Engineer с 5 годами опыта в информационной безопасности.
Специализация в аудите безопасности и penetration testing.

ОПЫТ РАБОТЫ:
- Security Engineer в SecureTech (2020-настоящее время)
  * Проведение аудитов безопасности
  * Penetration testing приложений
  * Настройка систем мониторинга безопасности
  * Работа с compliance требованиями

- Junior Security Analyst в CyberDefense (2019-2020)
  * Мониторинг безопасности
  * Анализ инцидентов
  * Работа с SIEM системами

ОБРАЗОВАНИЕ:
- Магистр информационной безопасности, МГУ (2019)
- Сертификат CISSP (2020)

НАВЫКИ:
Penetration Testing, Security Auditing, SIEM, Network Security, Compliance, CISSP, CEH, Burp Suite""",

    """Екатерина Орлова
Email: ekaterina.orlova@example.com
Телефон: +7-999-234-56-78
WhatsApp: +7-999-234-56-78

ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ:
Team Lead разработки с 8 годами опыта в разработке и руководстве командами.
Опыт управления командами до 10 человек.

ОПЫТ РАБОТЫ:
- Team Lead в TechLead (2021-настоящее время)
  * Руководство командой из 8 разработчиков
  * Архитектурное проектирование систем
  * Найм и онбординг новых сотрудников
  * Работа с продукт-менеджерами и stakeholders

- Senior Developer в DevTeam (2019-2021)
  * Разработка сложных систем
  * Менторинг junior разработчиков
  * Code review и техническое руководство

- Software Developer в VariousCompanies (2015-2019)
  * Разработка различных проектов
  * Работа с разными технологиями

ОБРАЗОВАНИЕ:
- Магистр программной инженерии, МГУ (2015)
- MBA, МГУ (2020)

НАВЫКИ:
Leadership, Team Management, Python, Java, Architecture, Agile, Scrum, Hiring, Mentoring"""
]

async def create_sample_data():
    """Create sample Russian data."""
    db = next(get_db())
    tools = AgentTools(db)
    
    print("Создание вакансий...")
    positions = []
    for i, vacancy_text in enumerate(VACANCIES, 1):
        try:
            position = tools.create_position(vacancy_text)
            positions.append(position)
            print(f"  ✓ Вакансия {i}/{len(VACANCIES)} создана: {position.structured_data.get('title', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Ошибка при создании вакансии {i}: {e}")
    
    print(f"\nСоздание резюме...")
    candidates = []
    for i, cv_text in enumerate(CVS, 1):
        try:
            # Save CV to temp file
            import tempfile
            import uuid
            from pathlib import Path
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(cv_text)
            temp_file.close()
            
            candidate = await tools.create_candidate_from_file(temp_file.name, 'txt')
            candidates.append(candidate)
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            profile = candidate.structured_profile or {}
            name = profile.get('name', 'N/A')
            print(f"  ✓ Резюме {i}/{len(CVS)} создано: {name}")
        except Exception as e:
            print(f"  ✗ Ошибка при создании резюме {i}: {e}")
    
    print(f"\n✅ Создано:")
    print(f"  - Вакансий: {len(positions)}")
    print(f"  - Кандидатов: {len(candidates)}")
    
    db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_sample_data())
