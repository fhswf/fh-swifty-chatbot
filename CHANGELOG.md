# CHANGELOG


## v0.7.0 (2025-10-23)

### Features

- Update user message autoscroll setting and rename assistant in UI
  ([`293ee6b`](https://github.com/fhswf/fh-swifty-chatbot/commit/293ee6bdb84d38397235937b3cfb194ba950ac7f))


## v0.6.0 (2025-10-23)

### Features

- Implement feedback and fallback mechanisms, including user feedback storage and mock replies
  during service outages
  ([`6f9cc5a`](https://github.com/fhswf/fh-swifty-chatbot/commit/6f9cc5a0cf76bec0ef29b7241ef1845a894f644c))

- Update feedback handling and fallback responses, including user input storage and improved mock
  replies
  ([`52fc0e0`](https://github.com/fhswf/fh-swifty-chatbot/commit/52fc0e05d8a384cd7773bf63eaeb537d7f1c3349))


## v0.5.0 (2025-10-10)

### Chores

- Update README to include new notebook and environment variable requirements, and enhance project
  structure with additional modules
  ([`a3d1e64`](https://github.com/fhswf/fh-swifty-chatbot/commit/a3d1e644716d31c5ddcb0dcd4052303f8db37be1))

### Features

- Enhance OpenAI API notebook with improved configuration validation and result analysis
  ([`6fdecc9`](https://github.com/fhswf/fh-swifty-chatbot/commit/6fdecc900edbe61d6a642b210fc1ac95fbbae775))


## v0.4.0 (2025-10-09)

### Features

- Add Jupyter notebook for OpenAI API blacklist checking functionality
  ([`e97baa6`](https://github.com/fhswf/fh-swifty-chatbot/commit/e97baa66549a6e639a3c9f60a0a764af939de984))


## v0.3.0 (2025-10-09)

### Chores

- Update README to reflect Python version requirement change from 3.7+ to 3.11+
  ([`d6e27f4`](https://github.com/fhswf/fh-swifty-chatbot/commit/d6e27f4b2c2641c56d2fc9eba75f080285a1d9de))

### Features

- Add PostgreSQL, Neo4j, Qdrant, and MinIO services to docker-compose
  ([`283c8dc`](https://github.com/fhswf/fh-swifty-chatbot/commit/283c8dc50d229b117a36ab871f866fc8005b232b))


## v0.2.0 (2025-09-28)

### Chores

- Rename chatbot service to swifty-ui in docker-compose
  ([`835aaa7`](https://github.com/fhswf/fh-swifty-chatbot/commit/835aaa7484df3f6038869ea38acb80e98d8f97e9))

- Revert replicas
  ([`8a2222d`](https://github.com/fhswf/fh-swifty-chatbot/commit/8a2222dae019200fe4a5ed0e933e2b4907b9b478))

- Update licence
  ([`c99814b`](https://github.com/fhswf/fh-swifty-chatbot/commit/c99814b3cb2f765c1dc5fb8b67ab2b1f7471e1fe))

- Update readme for version 0.1.5, add last update date, and enhance technology stack details
  ([`1530637`](https://github.com/fhswf/fh-swifty-chatbot/commit/153063735d08a887358d656796e57065cc3d4a12))

- Update readme to include UV commands for environment setup and application execution
  ([`12077ab`](https://github.com/fhswf/fh-swifty-chatbot/commit/12077ab25a8cb9b4317a1460709c7c04a6de4929))

### Features

- Implement crawler
  ([`28ef553`](https://github.com/fhswf/fh-swifty-chatbot/commit/28ef55350f7aae767c9f5c0b82a913dcf3fce477))

- Use http cache to download updates only
  ([`9e0708b`](https://github.com/fhswf/fh-swifty-chatbot/commit/9e0708bc75643fa77c33306d16670afbe6c6a22c))


## v0.1.5 (2025-09-18)

### Bug Fixes

- Increase resource limits
  ([`04f963b`](https://github.com/fhswf/fh-swifty-chatbot/commit/04f963b85ded7d2ff686a476b8528486af25c175))


## v0.1.4 (2025-09-18)

### Bug Fixes

- Set replicas to 4
  ([`d3489dc`](https://github.com/fhswf/fh-swifty-chatbot/commit/d3489dcd2e3bd9145af477fc33a795e225095639))

### Chores

- Add notebook dependency group in pyproject.toml for enhanced development environment
  ([`2670fb5`](https://github.com/fhswf/fh-swifty-chatbot/commit/2670fb58771711e6096d23f53f0369cc3cc42738))

- Update chainlit.md to reflect new welcome message and versioning
  ([`13c1345`](https://github.com/fhswf/fh-swifty-chatbot/commit/13c134582d8c7864531895617ac772e4fc603e47))

- Update Dockerfile to remove --no-dev flag from uv sync and clean up pyproject.toml by removing
  development dependencies
  ([`6089520`](https://github.com/fhswf/fh-swifty-chatbot/commit/60895204169a98c60ba316f59cad596a644c59bf))

- Update Dockerfile to use python:3.13 and bump fh-swifty-chatbot version to 0.1.3, adding
  beautifulsoup4 as a runtime dependency
  ([`cc07e88`](https://github.com/fhswf/fh-swifty-chatbot/commit/cc07e8834ff7675345144012fe8c8c1c405e2d17))

- Update Dockerfile to use python:3.13-slim
  ([`9a0f3c5`](https://github.com/fhswf/fh-swifty-chatbot/commit/9a0f3c5cde1c02471548a6cfd420e6bea7cdb576))


## v0.1.3 (2025-09-12)

### Bug Fixes

- Update pyproject.toml to add selenium and unstructured as development dependencies
  ([`1bd3007`](https://github.com/fhswf/fh-swifty-chatbot/commit/1bd3007f4e0ace4f9f45a2869f25797987693526))

### Chores

- Add Playwright and unstructured as dependencies in pyproject.toml and update urlLoader notebook to
  utilize PlaywrightURLLoader
  ([`19d7be8`](https://github.com/fhswf/fh-swifty-chatbot/commit/19d7be858b715f8259dff7f19cb6e9d9f4333319))

- Refactor web crawling implementation to use SeleniumURLLoader and update dependencies in
  pyproject.toml
  ([`9b5e1ef`](https://github.com/fhswf/fh-swifty-chatbot/commit/9b5e1ef1b843ce0f57c65d9d21ed0ee0051693d9))

- Remove BrowserConfig instantiation from AsyncWebCrawler usage in find_info_on_fhswf_website
  function
  ([`7fd7a8e`](https://github.com/fhswf/fh-swifty-chatbot/commit/7fd7a8e3cd0552d665ffb8a4f19cd7608d912038))

- Remove unnecessary browser_mode parameter from BrowserConfig in AsyncWebCrawler
  ([`d14629f`](https://github.com/fhswf/fh-swifty-chatbot/commit/d14629f8225b0de7045a4cebd3afcf1b5b6938b7))

- Update Dockerfile to use python:3.13-slim, add beautifulsoup4 as a runtime dependency, and replace
  SeleniumURLLoader with WebBaseLoader in tools.py
  ([`5e86957`](https://github.com/fhswf/fh-swifty-chatbot/commit/5e869572fea56d43818d567d05624ecef6add979))


## v0.1.2 (2025-09-12)

### Bug Fixes

- Update AsyncWebCrawler configuration to use BrowserConfig for headless browsing
  ([`ee9191e`](https://github.com/fhswf/fh-swifty-chatbot/commit/ee9191e82c70ba6751b794894b449ebbbdcfc6e7))

### Chores

- Add installation of system dependencies for Playwright Chromium in Dockerfile
  ([`a2c52b0`](https://github.com/fhswf/fh-swifty-chatbot/commit/a2c52b0cb5d10b720a7d4fbf35f28ad3bdac1bc5))

- Add system dependencies for Playwright Chromium in Dockerfile
  ([`6e0ce81`](https://github.com/fhswf/fh-swifty-chatbot/commit/6e0ce81607b5ed0d270bbdb7605aeb50d697745c))

- Refine Dockerfile by removing redundant cleanup step after installing system dependencies
  ([`7bd81b9`](https://github.com/fhswf/fh-swifty-chatbot/commit/7bd81b988b5132ba38b836c251b2ec08a7f7471c))

- Remove Playwright Chromium installation command from Dockerfile
  ([`4488060`](https://github.com/fhswf/fh-swifty-chatbot/commit/4488060948cc5321a047689ab189925070a0898a))

- Remove system dependencies installation for Playwright Chromium from Dockerfile
  ([`22a7cd0`](https://github.com/fhswf/fh-swifty-chatbot/commit/22a7cd050aae47eac704ed51b43881f794596773))

- Remove unnecessary dependencies from playwright installation command
  ([`da0d3c2`](https://github.com/fhswf/fh-swifty-chatbot/commit/da0d3c2ca8b62dcd7ddbb6c86bb22c846339eb1e))

- Restore Playwright Chromium installation command in Dockerfile
  ([`93e8414`](https://github.com/fhswf/fh-swifty-chatbot/commit/93e841485670ef62fef7a0c51063b877b102a7c6))

- Streamline system dependencies installation for Playwright Chromium in Dockerfile
  ([`7086737`](https://github.com/fhswf/fh-swifty-chatbot/commit/7086737df75f2fcd8b08fcbd7c76a50388ebb207))

- Switch to Alpine Python base image in Dockerfile
  ([`7526cdc`](https://github.com/fhswf/fh-swifty-chatbot/commit/7526cdc82056bebba262c0723eec43f17ddc33b3))

- Switch to slim Python base image in Dockerfile
  ([`3c99d82`](https://github.com/fhswf/fh-swifty-chatbot/commit/3c99d8210f6ae1f712eee5cfa3e01e5ea54892a6))

- Switch to standard Python base image in Dockerfile
  ([`4d0e2b7`](https://github.com/fhswf/fh-swifty-chatbot/commit/4d0e2b7a4fd7eb493f37eddde103efdb10d01a4e))

- Update Dockerfile to install additional system dependencies for Playwright Chromium
  ([`6a69ce4`](https://github.com/fhswf/fh-swifty-chatbot/commit/6a69ce426d11ea920f86fb69f9bbdb5accf82055))

- Update Dockerfile to streamline Playwright Chromium installation with dependencies
  ([`1ac3b9b`](https://github.com/fhswf/fh-swifty-chatbot/commit/1ac3b9bedd350df1f7596ef440e9bbfde3e24c25))

- Update playwright install command
  ([`162107d`](https://github.com/fhswf/fh-swifty-chatbot/commit/162107ddc538842ec09276e21d4c78face54f728))

- Update playwright installation command to include dependencies
  ([`ef317a1`](https://github.com/fhswf/fh-swifty-chatbot/commit/ef317a12c5d0d2a9fe01e93163a745dd28068441))

- Update playwright installation to use chromium and bump package version to 0.1.1
  ([`ee5297f`](https://github.com/fhswf/fh-swifty-chatbot/commit/ee5297f8bc185bbf03abe07c7b1a029d996ecf21))

- Update pyproject.toml and uv.lock to add development dependencies including ipykernel and related
  packages
  ([`f8a3a9c`](https://github.com/fhswf/fh-swifty-chatbot/commit/f8a3a9c2bc45f7ef457e839da9d308ce75e9bce3))


## v0.1.1 (2025-09-12)

### Bug Fixes

- Update API keys in k8s for correct encoding
  ([`b924c58`](https://github.com/fhswf/fh-swifty-chatbot/commit/b924c58b10b06609acfbb2db4df7498b494bce63))

### Chores

- Add Langsmith and Tavily keys to deployment
  ([`19857dd`](https://github.com/fhswf/fh-swifty-chatbot/commit/19857dd72c7f0679187530ac72085a565e364d4e))

- Add openai api key
  ([`812ddaf`](https://github.com/fhswf/fh-swifty-chatbot/commit/812ddafbdc1fcb59bc9324a26e6894606aa7ce5c))

- Enhance build script to include Docker login and push commands
  ([`c5e8364`](https://github.com/fhswf/fh-swifty-chatbot/commit/c5e836482094419ffe49adcf9a12216a6b101d38))

- Fix deployment files
  ([`ff7bd46`](https://github.com/fhswf/fh-swifty-chatbot/commit/ff7bd46c0fb036d68351246b4d6865cdf6310875))

- K8s deployment
  ([`7912578`](https://github.com/fhswf/fh-swifty-chatbot/commit/7912578592d205f7c89d84b18801596794ff8032))

- K8s deployment
  ([`a1b65a8`](https://github.com/fhswf/fh-swifty-chatbot/commit/a1b65a8e4ec9c5d883df58fc9baf182bc89c0f81))

- K8s deployment
  ([`7c7aeb6`](https://github.com/fhswf/fh-swifty-chatbot/commit/7c7aeb6a445ec758fe5429ccdb524885a9eecc28))

- Update build scripts and dependencies for Docker and Python environment
  ([`dc0aa09`](https://github.com/fhswf/fh-swifty-chatbot/commit/dc0aa096fe3084b72e5b4cc8e8170587ec664541))


## v0.1.0 (2025-09-12)

### Features

- Automatic docker build
  ([`1138fae`](https://github.com/fhswf/fh-swifty-chatbot/commit/1138fae7dd63ed9f984733fc76dcc72715ee6e55))
