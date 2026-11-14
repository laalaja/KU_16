# Граф зависимостей NuGet — вариант 16

Практическая работа по дисциплине «Конфигурационное управление».
Цель — построить и визуализировать граф зависимостей NuGet для выбранной версии пакета.

Программа строит граф прямых и транзитивных зависимостей указанной версии
пакета и печатает описание графа на языке D2. Источник: публичный индекс
NuGet v3 или локальный JSON. Для скачивания и анализа используются только
модули стандартной библиотеки Python; пакеты .NET не устанавливаются.

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

Код выхода 0 означает успех, 1 — ошибку при чтении или анализе данных,
2 — ошибку в аргументах. Сообщения об ошибках направляются в stderr.

| Коммит | Доступное поведение |
| --- | --- |
| `feat(cli)` | Печать проверенных параметров в формате `ключ=значение`. |
| `feat(nuget)` | Печать прямых зависимостей из манифеста. |
| `feat(graph)` | Текстовый список рёбер графа DFS. |
| `feat(reverse)` | Список рёбер или обратные зависимости по флагу `--reverse`. |
| `feat(d2)` | Описание графа D2 в stdout (текущая версия). |

Для проверки этапа без переключения текущей ветки:

```text
git log --oneline
git worktree add --detach ../stage-4 ":/^feat(reverse):"
```

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

## Этап 4 — обратные зависимости

Демонстрация относится к коммиту `feat(reverse)`. Флаг `--reverse`
доступен только на этапе 4, вместе с `--test-mode`.

Программа меняет направление всех рёбер тестового репозитория и применяет
тот же DFS от указанного пакета и версии. Печатает как прямых, так и
транзитивных потребителей, до заданной глубины. Сам корень в список
не попадает даже при цикле. Индекс NuGet v3 не предоставляет полного списка
входящих рёбер, поэтому этот режим работает с локальным описанием графа.

```text
python src --package A --version 1 --test-mode --repository examples/repository.json --reverse --max-depth 1
python src --package A --version 1 --test-mode --repository examples/repository.json --reverse --max-depth 2
python src --package D --version 1 --test-mode --repository examples/repository.json --reverse --max-depth 2
python src --package G --version 1 --test-mode --repository examples/repository.json --reverse
```

Для `A` на глубине 1 выводятся `C` и `E`, на глубине 2 добавляется
`F`. Для `D` выводятся `B` и `A`. Для `G` обратных зависимостей нет.

## Этап 5 — D2

```text
python src --package A --version 1 --test-mode --repository examples/repository.json --max-depth 2
```

Каждая вершина отображается с точной версией; стрелка идёт от потребителя
к зависимости. Корневой пакет выделен цветом. Для получения SVG можно
сохранить stdout и запустить [D2](https://d2lang.com/):

```text
python src --package A --version 1 --test-mode --repository examples/repository.json > graph.d2
d2 graph.d2 graph.svg
```

В Windows PowerShell 5 вместо перенаправления `>` используйте
`| Set-Content -Encoding UTF8 graph.d2`.

### Три примера из NuGet.org

```text
python src --package Microsoft.Extensions.Primitives --version 8.0.0 --max-depth 1 > primitives.d2
python src --package Microsoft.Extensions.Configuration.Abstractions --version 8.0.0 --max-depth 2 > configuration.d2
python src --package Microsoft.Extensions.DependencyInjection.Abstractions --version 8.0.0 --max-depth 1 > dependency-injection.d2
d2 primitives.d2 primitives.svg
d2 configuration.d2 configuration.svg
d2 dependency-injection.d2 dependency-injection.svg
```

В таблице опущен общий префикс имён `Microsoft.Extensions.`.
Результаты сверены с вкладкой **Dependencies** официального NuGet Gallery
для тех же версий, в том числе при просмотре только группы `net8.0`.

| Пакет 8.0.0 | Наш граф: прямые зависимости | NuGet Gallery: группа `net8.0` |
| --- | --- | --- |
| [Primitives][primitives] | `System.Memory@4.5.5`, `System.Runtime.CompilerServices.Unsafe@6.0.0` | Нет |
| [Configuration.Abstractions][configuration] | `Primitives@8.0.0`, `System.ValueTuple@4.5.0` | `Primitives (≥ 8.0.0)` |
| [DependencyInjection.Abstractions][injection] | `Microsoft.Bcl.AsyncInterfaces@8.0.0`, `System.Threading.Tasks.Extensions@4.5.4` | Нет |

Все прямые рёбра совпадают с объединением групп NuGet Gallery. Gallery
показывает ограничения версий; программа подписывает конкретные версии.
В группе `net8.0` рёбер меньше: например, `Configuration.Abstractions`
объявляет `System.ValueTuple` только в группе .NET Framework 4.6.2.

На глубине 2 в графе `Configuration.Abstractions` есть три ребра второго
уровня: два от `Primitives` из его групп .NET Framework / .NET Standard
и `System.ValueTuple@4.5.0 → NETStandard.Library@1.6.1` из группы
.NET Standard 1.0 самого [System.ValueTuple][tuple]. Это граф объявлений
всех групп: такая цепочка не означает, что один целевой проект использует
одновременно .NET Framework 4.6.2 и .NET Standard 1.0.

[primitives]: https://www.nuget.org/packages/Microsoft.Extensions.Primitives/8.0.0#dependencies-body-tab
[configuration]: https://www.nuget.org/packages/Microsoft.Extensions.Configuration.Abstractions/8.0.0#dependencies-body-tab
[injection]: https://www.nuget.org/packages/Microsoft.Extensions.DependencyInjection.Abstractions/8.0.0#dependencies-body-tab
[tuple]: https://www.nuget.org/packages/System.ValueTuple/4.5.0#dependencies-body-tab

### Устройство программы

Роли модулей: `config.py` проверяет аргументы; `nuget.py` читает индекс
и манифесты; `version.py` и `requirements.py` нормализуют и подбирают
версии; `local.py` читает тестовый JSON; `graph.py` реализует DFS;
`d2.py` формирует вывод; `cli.py` связывает эти операции.

Для сдачи создайте пустой публичный репозиторий, добавьте его адрес
через `git remote add origin URL` и отправьте все пять этапов командой
`git push -u origin main`.
