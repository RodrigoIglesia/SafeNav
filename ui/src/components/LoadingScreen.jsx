// src/components/LoadingScreen.jsx

export default function LoadingScreen({ message = "Loading SafeNav map..." }) {
  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <div style={styles.spinner}></div>
        <p style={styles.text}>{message}</p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    width: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f8f9fa",
  },
  content: {
    textAlign: "center",
  },
  text: {
    marginTop: "1rem",
    fontSize: "1.1rem",
    color: "#333",
  },
  spinner: {
    width: "40px",
    height: "40px",
    border: "4px solid #ddd",
    borderTop: "4px solid #007bff",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
  },
};