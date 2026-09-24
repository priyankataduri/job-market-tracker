with jobs as (
    select
        job_id,
        role_family,
        date_trunc('week', posted_date) as week
    from {{ ref('int_jobs_deduped') }}
),

totals as (
    select week, role_family, count(*) as total_postings
    from jobs
    group by 1, 2
),

skill_counts as (
    select
        j.week,
        j.role_family,
        s.skill,
        s.skill_category,
        count(distinct s.job_id) as postings
    from {{ ref('int_job_skills') }} s
    join jobs j using (job_id)
    group by 1, 2, 3, 4
)

select
    sc.week,
    sc.role_family,
    sc.skill,
    sc.skill_category,
    sc.postings,
    t.total_postings,
    round(100.0 * sc.postings / t.total_postings, 1) as pct_of_postings
from skill_counts sc
join totals t
    on sc.week = t.week and sc.role_family = t.role_family
    