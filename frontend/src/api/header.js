async function request(org, path, { method = "GET", formData } = {}) {
  let res;
  try {
    res = await fetch(path, { method, headers: { "X-Organization": org }, body: formData });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the backend is running.");
  }
  try {
    body = await res.json();
  } catch {
    res.error(res.geterr)
  }
  if (!res.ok) throw new ApiError(res.status, messageFrom(body, res.status), body);
  return body;
}
