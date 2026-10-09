# Microsoft Fabric implementation path

The local pipeline is the executable reference implementation. To move it to Fabric:

1. Create a Lakehouse and upload the five generated `data/csv` files to `Files/motorsport_bi/`.
2. Create a Fabric Pipeline with a Copy activity for the pinned F1DB release into Bronze storage. Record release version and SHA-256 in a control table.
3. Use a notebook or Dataflow Gen2 to implement the `src/build.py` transformations into Silver dimension and fact Delta tables. Keep the race-result grain and reject duplicate `(race_id, driver_id)` keys.
4. Run the checks in `src/build.py` as a pipeline quality gate. Stop semantic-model refresh if a check fails.
5. Create a Warehouse or Lakehouse SQL endpoint view equivalent to `sql/views.sql` and connect the Power BI semantic model in import or Direct Lake mode as appropriate.
6. Schedule refresh after each chosen source release and monitor failures and row-count drift.

This is a deployment design, not a claim that Fabric resources or pipelines were created. Fabric requires a tenant/workspace and appropriate capacity or trial.

