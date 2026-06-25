// Fetch job posting via Voyager API — replace [JOB_ID] and [CSRF] before running
(async function() {
  const jobId = '[JOB_ID]';
  const csrf = '[CSRF]';
  const url = `https://www.linkedin.com/voyager/api/jobs/jobPostings/${jobId}?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65`;
  try {
    const resp = await fetch(url, {
      headers: {
        'accept': 'application/vnd.linkedin.normalized+json+2.1',
        'csrf-token': csrf,
        'x-restli-protocol-version': '2.0.0',
      },
      credentials: 'include'
    });
    if (!resp.ok) return { status: resp.status, error: true };
    const data = await resp.json();
    const d = data?.data || data;
    const desc = d?.description?.text || d?.description?.attributedBody?.text || null;
    const listedAt = d?.listedAt || null;
    const title = d?.title || null;
    const companyName = d?.companyDetails?.['com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany']?.companyResolutionResult?.name || null;
    return { status: resp.status, desc, listedAt, title, companyName };
  } catch(e) {
    return { error: e.message };
  }
})()
