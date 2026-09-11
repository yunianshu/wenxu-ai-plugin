# Packaging guidance

## Evidence priority

1. 用户本次明确的交付目标、版本与授权。
2. 当前成功的项目发布流程或 CI 配置。
3. 已核实的项目文档、构建清单与工具链惯例。

## Common outputs

| Project | Typical command | Typical artifact |
| --- | --- | --- |
| Android Gradle | `gradlew assembleRelease` or `bundleRelease` | APK or AAB under module build outputs |
| Flutter | `flutter build apk --release` or `appbundle` | APK or AAB under Flutter build outputs |
| Spring Boot/Gradle | `gradlew bootJar` | executable JAR |
| Maven | `mvn package` | JAR or WAR under target |
| Node/Web | repository build script | deployable dist/build directory archive |
| Rust | `cargo build --release` | target/release binary |
| Go | repository build command | platform executable |

The table supplies discovery hints only. Never replace a repository-specific release pipeline with a guessed command.

仅用户或项目明确采用服务部署包契约时使用单顶层目录 tar.gz。原生 APK/AAB/JAR/WAR 等按请求直接交付，不自动套归档或增加生命周期脚本。已有容器、云平台或原生发布链优先；不要为满足本参考而替换部署方式。
