import { useEffect, useState } from "react";
import { getHelloMessage, getSchools } from "./services/api";

function App() {
  const [message, setMessage] = useState("Loading...");
  const [schools, setSchools] = useState([]);

  useEffect(() => {
    getHelloMessage()
      .then(data => setMessage(data.message))
      .catch(() => setMessage("Error connecting to FastAPI"));

    getSchools()
      .then(data => setSchools(data))
      .catch(err => console.error("Failed to fetch schools", err));
  }, []);

  return (
    <div>
      <h1>FastAPI + React</h1>
      <p>{message}</p>
      <ul>
        {schools.map(s => (
          <li key={s.id}>{s.school_name}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
