window.APP_CONFIG = {
  API_BASE: window.location.hostname === "localhost" 
    ? "http://localhost:8000" 
    : `https://${window.location.hostname}/api`
};
