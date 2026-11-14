# Граф зависимостей NuGet — вариант 16

Практическая работа по дисциплине «Конфигурационное управление».
Цель — построить и визуализировать граф зависимостей NuGet для выбранной версии пакета.

На этапе 3 программа строит граф прямых и транзитивных зависимостей
из публичного источника NuGet v3 либо из локального тестового репозитория.

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

Отдельная печать прямых объявлений доступна в коммите `feat(nuget)`.

```text
python src --package Microsoft.Extensions.Configuration.Abstractions --version 8.0.0
```

Программа находит `PackageBaseAddress/3.0.0` в индексе, скачивает `.nuspec`
строго для указанной версии и выводит столбцы «пакет», «ограничение версии»
и «целевая платформа». Для пакета без зависимостей выводится сообщение.
На этом этапе глубина не используется; тестовый граф читается с этапа 3.
Неизвестная версия, недоступный индекс или ошибочный манифест дают код 1.

[Описание NuGet API](https://learn.microsoft.com/nuget/api/package-base-address-resource)

## Этап 3 — итеративный DFS

Обход использует стек и хранит самую малую глубину, на которой уже обработан
каждый узел. Возврат по циклу сохраняет ребро и не повторяет обработку узла.
Если узел позднее найден более коротким путём, его допустимые потомки
пересчитываются. Узлы на границе глубины отображаются без исходящих рёбер.

Для сетевого источника программа объединяет объявления всех платформ.
Для каждого ограничения отдельно выбирается минимальная подходящая версия
из списка версий источника. Предварительные версии учитываются, если их
указывает граница диапазона или корень задан предварительной версией.
Граф может содержать несколько версий одного пакета. Это анализ метаданных,
а не восстановление проекта: совместимость платформ, конфликты версий
между ветвями и статус публикации версии не учитываются.

В тестовом файле первый уровень — имена из заглавных латинских букв,
второй — точные версии, третий — словарь «имя зависимости: точная версия».
Зависимости должны ссылаться на объявленные узлы. Например:

```json
{"A":{"1.0.0":{"B":"1.0.0"}},"B":{"1.0.0":{}}}
```

Примеры для `examples/repository.json`:

```text
python src --package A --version 1 --test-mode --repository examples/repository.json --max-depth 0
python src --package A --version 1 --test-mode --repository examples/repository.json --max-depth 1
python src --package A --version 1 --test-mode --repository examples/repository.json --max-depth 2
python src --package G --version 1 --test-mode --repository examples/repository.json
python src --package A --version 2 --test-mode --repository examples/repository.json
```

При глубине 0 виден только `A`. При глубине 1: `A → B`, `A → C`.
При глубине 2 также видны `B → D` и замыкающее цикл ребро `C → A`.
`G` — изолированный узел. Запрос отсутствующей версии `A@2.0.0`
завершается с кодом 1.
