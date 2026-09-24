with ranked as (
    select
        *,
        row_number() over (
            partition by lower(title), lower(coalesce(company, '')), lower(coalesce(location, ''))
            order by created_at
        ) as rn
    from {{ ref('stg_job_postings') }}
)

select
    job_id,
    title,
    company,
    location,
    state,
    posted_date,
    created_at,
    salary_min,
    salary_max,
    redirect_url,
    lower(title || ' ' || coalesce(description, '')) as search_text,
    case
        when lower(title) like '%analytics engineer%' then 'Analytics Engineer'
        when lower(title) like '%data engineer%'      then 'Data Engineer'
        when lower(title) like '%data analyst%'       then 'Data Analyst'
        else 'Other'
    end as role_family
from ranked
where rn = 1
