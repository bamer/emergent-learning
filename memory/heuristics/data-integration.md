# Heuristics: data-integration

Generated from failures, successes, and observations in the **data-integration** domain.

---

## H-291: SambaPOS backup extraction: Use Docker with MSSQL Server image to restore .bak files. The process requires: 1) Pull mssql/server:2019-latest image, 2) Start container with ACCEPT_EULA and SA_PASSWORD, 3) Copy backup file to container, 4) Use sqlcmd to RESTORE DATABASE with MOVE clauses for logical file names, 5) Extract data with SELECT queries to CSV.

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-16

Successfully extracted 8 years of restaurant data (184,617 orders, 342 menu items) from SambaPOS5_Full.bak using Docker MSSQL container.

---

