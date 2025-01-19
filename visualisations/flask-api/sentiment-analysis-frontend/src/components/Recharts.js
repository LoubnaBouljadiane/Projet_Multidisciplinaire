import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";

function Recharts({ data }) {
  const sentimentCounts = data.reduce((acc, comment) => {
    acc[comment.sentiment] = (acc[comment.sentiment] || 0) + 1;
    return acc;
  }, {});

  const chartData = Object.keys(sentimentCounts).map(sentiment => ({
    name: sentiment,
    count: sentimentCounts[sentiment],
  }));

  return (
    <div>
      <h3>Sentiment Distribution</h3>
      <BarChart width={600} height={300} data={chartData}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill="#8884d8" />
      </BarChart>
    </div>
  );
}

export default Recharts;
