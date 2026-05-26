# X-Forwarded-For через цепочку nginx

Стенд показывает, как очищать пользовательский `X-Forwarded-For` на входе и собирать новую цепочку из IP пользователя и nginx-прокси.

В compose есть три nginx и простое HTTP-приложение на Python. Приложение выводит полученный заголовок `X-Forwarded-For`.

## Схема

Контейнеры в сети `172.28.0.0/24`:

| Сервис | IP | Порт на хосте |
|---|---:|---:|
| app | `172.28.0.10` | нет |
| nginx1 | `172.28.0.11` | `8081` |
| nginx2 | `172.28.0.12` | `8082` |
| nginx3 | `172.28.0.13` | `8083` |

Маршруты:

| URL | Цепочка |
|---|---|
| `http://localhost:8081/app` | пользователь, nginx1, app |
| `http://localhost:8082/app` | пользователь, nginx2, app |
| `http://localhost:8083/app` | пользователь, nginx3, app |
| `http://localhost:8082/to-nginx3` | пользователь, nginx2, nginx3, app |
| `http://localhost:8081/to-nginx2-nginx3` | пользователь, nginx1, nginx2, nginx3, app |

## Как работает защита

Файл `nginx/00-xff.conf` считает доверенными только IP трех nginx:

```nginx
172.28.0.11
172.28.0.12
172.28.0.13
```

Если запрос пришел не от этих адресов, nginx игнорирует входящий `X-Forwarded-For` и создает новый:

```text
IP_пользователя, IP_текущего_nginx
```

Если запрос пришел от доверенного nginx, текущий nginx сохраняет старую цепочку и добавляет свой IP:

```text
старая_цепочка, IP_текущего_nginx
```

## Запуск

```bash
docker compose up --build -d
```

## Протокол тестирования curl

В примерах ниже первый IP обычно `172.28.0.1`. Это IP Docker gateway, с которого nginx видит запрос с хоста.

### 1. Вход через nginx1

```bash
curl -s http://localhost:8081/app
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.11
```

### 2. Вход через nginx2

```bash
curl -s http://localhost:8082/app
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.12
```

### 3. Вход через nginx3

```bash
curl -s http://localhost:8083/app
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.13
```

### 4. Цепочка nginx2, nginx3

```bash
curl -s http://localhost:8082/to-nginx3
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.12, 172.28.0.13
```

### 5. Цепочка nginx1, nginx2, nginx3

```bash
curl -s http://localhost:8081/to-nginx2-nginx3
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.11, 172.28.0.12, 172.28.0.13
```

### 6. Поддельный заголовок не проходит

```bash
curl -s -H 'X-Forwarded-For: 1.2.3.4, 5.6.7.8' http://localhost:8081/to-nginx2-nginx3
```

Ожидаемый `x_forwarded_for`:

```text
172.28.0.1, 172.28.0.11, 172.28.0.12, 172.28.0.13
```

В ответе не должно быть `1.2.3.4` и `5.6.7.8`.
