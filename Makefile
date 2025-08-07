help:
	@echo "システムを実行する"
	@echo " $$ make run"
	@echo "Pytestを実行する"
	@echo " $$ make test"
	@echo "全てのソースコードをフォーマットする"
	@echo " $$ make format"
	@echo "全てのソースコードのスタイルをチェックする"
	@echo " $$ make check_style"
	@echo "カバレッジレポートの表示"
	@echo " $$ make coverage"
	@echo "サーバを起動"
	@echo " $$ make server"

run:
	uv run src

test:
	uv run pytest

format:
	uv run autopep8 -i -r src/ tests/

check_style:
	uv run pycodestyle src/ tests/
	uv run pydocstyle src/ tests/

coverage:
	uv run coverage run -m pytest
	uv run coverage report

server:
	uv run -m src.server.fastapi_server
