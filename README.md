# Plano de Independência

Aplicação privada de planejamento para organizar a saída de casa: itens, preços, links de produtos, valores pagos e total já investido.

## Stack
- React + TypeScript + Vite
- FastAPI + SQLAlchemy 2
- PostgreSQL
- Alembic
- Docker Compose

## Executar
1. Instale Docker + Docker Compose.
2. Na raiz do projeto execute:
   ```bash
   docker compose up --build
   ```
3. Abra `http://localhost:5173`.
4. API/Swagger: `http://localhost:8000/docs`.

O backend aplica a migration Alembic automaticamente na inicialização.

## Dados
Os dados ficam persistidos no volume PostgreSQL `postgres_data`. O total **Já investido na casa** é calculado pela soma de `valor_pago` dos itens cadastrados.

## Segurança
Não há autenticação nesta V1. Não exponha a aplicação diretamente à internet sem uma camada de acesso restrito na hospedagem.
