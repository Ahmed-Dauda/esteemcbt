import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL;
// console.log("API base URL:", API_BASE_URL); // ✅ Confirm this shows the correct value

export const getHelloMessage = async () => {
  const res = await axios.get(`${API_BASE_URL}/ping/`);
  return res.data;
};

export const getSchools = async () => {
  const res = await axios.get(`${API_BASE_URL}/school/`);
  return res.data;
};
