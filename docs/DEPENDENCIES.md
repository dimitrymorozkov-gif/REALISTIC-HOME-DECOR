# Подтверждённые зависимости

Проверено 25 октября 2026 года по официальным метаданным и реальной сборкой.
Зависимости закреплены в `gradle.properties` и Gradle wrapper; SNAPSHOT-версии
не используются.

| Компонент | Закреплённая версия | Подтверждение |
|---|---|---|
| Minecraft | 1.21.11 | Официальный manifest и загруженный `version.json`; Java21, resource pack75.0, data pack94.1 |
| Fabric Loader | 0.20.1 | Официальный Fabric Meta помечает выпуск стабильным и совместимым с1.21.11 |
| Fabric API | 0.141.6+1.21.11 | Официальная ветка Fabric1.21.11 и разрешённый Maven-артефакт |
| Fabric Loom | 1.14.10 | Официальный Gradle module указывает JVM21 и Gradle API9.2.0 |
| Gradle | 9.2.1 | Официальный wrapper; SHA-256 дистрибутива закреплён |
| Разработка | JDK21; Python3.10+ | Сборка использует `--release21`; генератор работает без сторонних Python-пакетов |

Первоначально проверен современный Loom1.19.3: ему требуется Java25. Для
Minecraft1.21.11 выбран совместимый стабильный Loom1.14.10 с Java21.

Источники:

- https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
- https://meta.fabricmc.net/v2/versions/loader/1.21.11
- https://maven.fabricmc.net/net/fabricmc/fabric-loom/1.14.10/fabric-loom-1.14.10.module
- https://raw.githubusercontent.com/FabricMC/fabric/1.21.11/gradle.properties
- https://services.gradle.org/distributions/gradle-9.2.1-bin.zip.sha256
- https://docs.fabricmc.net/

Runtime-зависимости мода — Minecraft, Java21, Fabric Loader и Fabric API.
Не используются сторонние библиотеки анимации, собственный рендерер, Mixins
или постоянно обновляемые Block Entity.

В подготовленной облачной среде установлен Eclipse Temurin21.0.13+9
в `/workspace/.tools/jdk-21.0.13+9`, поскольку базовая Java не содержала
исполняемого `javac`. Архив получен из официального релиза Adoptium;
проверенный SHA-256:

```text
d7f5d5cf865a2902b70ff549b97586a7d3f234e016f041ab447ea740c7d66d1c
```

URL:
https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz

Для повторения сетевых операций в управляемой среде нужны
`meta.fabricmc.net`, `maven.fabricmc.net`, `piston-meta.mojang.com`,
`piston-data.mojang.com`, `libraries.minecraft.net`,
`resources.download.minecraft.net` и домены стандартных пакетных репозиториев.
Дополнительных секретов проект не требует.
