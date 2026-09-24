select
    j.job_id,
    s.skill,
    s.category as skill_category
from {{ ref('int_jobs_deduped') }} j
join {{ ref('skills') }} s
    on regexp_matches(j.search_text, s.pattern)
    