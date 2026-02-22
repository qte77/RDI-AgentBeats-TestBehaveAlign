SELECT
    json_extract_string(to_json(participants), '$.' || list_extract(json_keys(to_json(participants)), 1)) AS id,
    json_extract_string(to_json(res), '$.task_rewards.track') AS "Track",
    ROUND(COALESCE(json_extract(to_json(res), '$.score')::DOUBLE, 0), 2) AS "Score",
    ROUND(COALESCE(json_extract(to_json(res), '$.task_rewards.mutation_score')::DOUBLE, 0) * 100, 1) AS "Mutation %",
    ROUND(COALESCE(json_extract(to_json(res), '$.task_rewards.fault_detection_rate')::DOUBLE, 0) * 100, 1) AS "Fault Detection %",
    ROUND(COALESCE(json_extract(to_json(res), '$.pass_rate')::DOUBLE, 0), 1) AS "Pass Rate",
    COALESCE(json_extract(to_json(res), '$.task_rewards.task_count')::INTEGER, 0) AS "# Tasks"
FROM results
CROSS JOIN UNNEST(results) AS r(res)
ORDER BY "Score" DESC, "Mutation %" DESC;
