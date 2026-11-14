# Граф зависимостей NuGet — вариант 16

Практическая работа по дисциплине «Конфигурационное управление».
Цель — построить и визуализировать граф зависимостей NuGet для выбранной версии пакета.

На этапе 2 программа читает публичный индекс NuGet v3 и манифест
`.nuspec` указанной версии, затем печатает прямые зависимости.

## Запуск

Нужен Python 3.10 или новее. Дополнительные пакеты и сборка не нужны.
Запуск из корня репозитория: `python src`, `run.bat` (Windows)
или `./run.sh` (Unix). Для предварительной проверки синтаксиса:
`python -m compileall -q src tests`.

```text
python -m unittest discover -s tests -v
python src --help
```

| Опция | Назначение |
| --- | --- |
| `--package ID` | Обязательное имя пакета; в тестовом режиме — заглавные латинские буквы. |
| `--version VERSION` | Обязательная точная версия, например `1.0.0`. |
| `--repository URL_OR_PATH` | URL индекса NuGet v3 (по умолчанию nuget.org) либо путь к тестовому файлу. |
| `--test-mode` | Читать тестовый файл; наличие флага включает режим, значение ему не передаётся. |
| `--max-depth N` | Целое неотрицательное число; по умолчанию 3. Корень имеет глубину 0. |

## Этап 1 — прототип CLI

Эти примеры относятся к коммиту `feat(cli)`: на этапе 1 программа
печатала итоговые значения в формате `ключ=значение`.

```text
python src --package example --version 1.0.0
python src --package A --version 1.0 --test-mode --repository examples/repository.json --max-depth 0
```

Вторая команда выводит:

```text
package=A
repository=examples/repository.json
test_mode=True
version=1.0
max_depth=0
```

Демонстрация ошибок (каждая команда завершается с кодом 2):

```text
python src --package bad/name --version 1.0
python src --package A --version "[1,)"
python src --package A --version 1.0 --repository ftp://example.org
python src --package A --version 1.0 --test-mode --repository missing.json
python src --package A --version 1.0 --test-mode false
python src --package A --version 1.0 --max-depth -1
```

## Этап 2 — получение метаданных NuGet

```text
python src --package Microsoft.Extensions.Configuration.Abstractions --version 8.0.0
```

Программа находит `PackageBaseAddress/3.0.0` в индексе, скачивает `.nuspec`
строго для указанной версии и выводит столбцы «пакет», «ограничение версии»
и «целевая платформа». Для пакета без зависимостей выводится сообщение.
На этом этапе глубина не используется; тестовый граф читается с этапа 3.
Неизвестная версия, недоступный индекс или ошибочный манифест дают код 1.

[Описание NuGet API](https://learn.microsoft.com/nuget/api/package-base-address-resource)
