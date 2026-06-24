/**
 * fetch_job_posting.js
 *
 * What it does:
 *   Fetches the full details of a single LinkedIn job posting via the Voyager API
 *   using a harvested job ID and the CSRF token extracted by extract_csrf.js.
 *   Returns title, company, location, remote flag, listing date, and the full JD text.
 *
 * Called from:
 *   scout-link SKILL.md — Step 4: called once per job card inside the fetch loop.
 *   Runs after harvest_job_ids.js has collected all job IDs from the page.
 *
 * Before running:
 *   Replace [JOB_ID] with the numeric job ID from harvest_job_ids.js results.
 *   Replace [CSRF] with the token returned by extract_csrf.js.
 *
 * Returns (as the last evaluated expression):
 *   JSON string with fields:
 *     status       — HTTP response status code (200 = success)
 *     title        — job title
 *     company      — hiring company name
 *     loc          — formatted location string (e.g. "Calgary, Alberta, Canada")
 *     remoteAllowed — boolean, true if the role allows remote work
 *     listedAt     — Unix timestamp (ms) when the posting was listed
 *     descLen      — character length of the JD text (useful for truncation checks)
 *     desc         — full job description text
 */

const jobId = '[JOB_ID]'; // ← replace [JOB_ID] with the actual job ID before running

// Call the Voyager API endpoint for full job posting data.
// Think of decorationId as a template that tells LinkedIn which fields to include
// in the response — similar to selecting columns in a SQL query.
// WebFullJobPosting-65 is the decoration that includes the full JD description text.
const response = await fetch(
  `/voyager/api/jobs/jobPostings/${jobId}?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65`,
  {
    headers: {
      // Tell the API we want the normalized JSON format (LinkedIn's internal API format).
      'accept': 'application/vnd.linkedin.normalized+json+2.1',
      // Required CSRF token — must match the active browser session cookie.
      'csrf-token': '[CSRF]',
      // Use REST protocol version 2.0.0 for this API endpoint.
      'x-restli-protocol-version': '2.0.0',
    },
    // Send browser cookies with the request so LinkedIn sees us as authenticated.
    credentials: 'include',
  }
);

const responseData = await response.json();

// The main job data lives in responseData.data.
const jobData = responseData?.data;
// If title or company comes back as undefined, it likely means the CSRF token has
// expired or the decorationId has changed — re-run extract_csrf.js and verify the API URL.

// Company info is in responseData.included (an array of related entities).
// We find the first entry whose $type string contains 'Company'.
// Each `?.` means "if the value on the left is null or undefined, stop here and
// return undefined instead of throwing a TypeError."
const companyName = responseData?.included
  ?.find(entity => entity.$type?.includes('Company'))?.name;

// Serialize the fields we care about into a JSON string for easy parsing by the skill.
JSON.stringify({
  status: response.status,
  title: jobData?.title,
  company: companyName,
  loc: jobData?.formattedLocation,
  remoteAllowed: jobData?.workRemoteAllowed,
  listedAt: jobData?.listedAt,
  descLen: jobData?.description?.text?.length,
  desc: jobData?.description?.text,
});
