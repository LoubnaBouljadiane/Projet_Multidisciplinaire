import React, { useState, useEffect } from "react";
import { fetchComments } from "./api";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./App.css";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"]; // Colors for the pie chart

function App() {
  const [comments, setComments] = useState([]);
  const [filteredComments, setFilteredComments] = useState([]);
  const [sourceFilter, setSourceFilter] = useState([]);
  const [sentimentFilter, setSentimentFilter] = useState([]);
  const [topicFilter, setTopicFilter] = useState([]);
  const [dateRange, setDateRange] = useState([null, null]);
  const [startDate, endDate] = dateRange;

  useEffect(() => {
    async function getData() {
      const data = await fetchComments();
      setComments(data);
      setFilteredComments(data);
    }
    getData();
  }, []);

  useEffect(() => {
    const filterData = () => {
      let filtered = comments;

      if (sourceFilter.length) {
        filtered = filtered.filter((comment) =>
          sourceFilter.includes(comment.source)
        );
      }
      if (sentimentFilter.length) {
        filtered = filtered.filter((comment) =>
          sentimentFilter.includes(comment.sentiment)
        );
      }
      if (topicFilter.length) {
        filtered = filtered.filter((comment) =>
          topicFilter.includes(comment.topic)
        );
      }
      if (startDate && endDate) {
        filtered = filtered.filter(
          (comment) =>
            new Date(comment.date) >= startDate && new Date(comment.date) <= endDate
        );
      }

      setFilteredComments(filtered);
    };
    filterData();
  }, [sourceFilter, sentimentFilter, topicFilter, startDate, endDate, comments]);

  // Prepare data for charts
  const sentimentCount = filteredComments.reduce((acc, comment) => {
    acc[comment.sentiment] = (acc[comment.sentiment] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.keys(sentimentCount).map((key) => ({
    name: key,
    value: sentimentCount[key],
  }));

  const lineData = filteredComments.map((comment, index) => ({
    name: `Comment ${index + 1}`,
    sentimentValue: comment.sentiment === "POSITIVE" ? 1 : comment.sentiment === "NEGATIVE" ? -1 : 0,
  }));

  const barData = Object.entries(sentimentCount).map(([key, value]) => ({
    sentiment: key,
    count: value,
  }));

  return (
    <div>
        <header>
        <h1 className="text-center">📊 Sentiment Analysis Report</h1>
        <h3> Summary statistics</h3>
        <div className="container">
          <table className="table table-striped table-bordered mx-auto" style={{ width: '90%' }}>
            <thead className="table-light">
              <tr>
                <th className="b">📝 Number of Comments</th>
                <th className="b">📌 Number of Topics</th>
                <th className="b">🔗 Number of Sources</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="a">{filteredComments.length}</td>
                <td className="a">{new Set(filteredComments.map((comment) => comment.topic)).size}</td>
                <td className="a">{new Set(filteredComments.map((comment) => comment.source)).size}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </header>
          

      <div>
        <h3>Filters</h3>
        <div>
          <label>Source: </label>
          <select
            multiple
            onChange={(e) =>
              setSourceFilter(
                Array.from(e.target.selectedOptions, (option) => option.value)
              )
            }
          >
            {Array.from(new Set(comments.map((comment) => comment.source))).map(
              (source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              )
            )}
          </select>
        </div>

        <div>
          <label>Sentiment: </label>
          <select
            multiple
            onChange={(e) =>
              setSentimentFilter(
                Array.from(e.target.selectedOptions, (option) => option.value)
              )
            }
          >
            {Array.from(
              new Set(comments.map((comment) => comment.sentiment))
            ).map((sentiment) => (
              <option key={sentiment} value={sentiment}>
                {sentiment}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Topic: </label>
          <select
            multiple
            onChange={(e) =>
              setTopicFilter(
                Array.from(e.target.selectedOptions, (option) => option.value)
              )
            }
          >
            {Array.from(new Set(comments.map((comment) => comment.topic))).map(
              (topic) => (
                <option key={topic} value={topic}>
                  {topic}
                </option>
              )
            )}
          </select>
        </div>

        <div className="filter-group">
            <label>Date Range: </label>
            <DatePicker
              selectsRange
              startDate={startDate}
              endDate={endDate}
              onChange={(update) => setDateRange(update)}
              isClearable
              dateFormat="yyyy/MM/dd"  // Vous pouvez changer le format selon votre préférence
              className="datepicker-input"  // Assurez-vous que ce style est appliqué
            />
          </div>

      </div>

      {/* Pie Chart */}
      <h3>Pie Chart - Sentiment Distribution</h3>
      <PieChart width={400} height={400}>
        <Pie
          data={pieData}
          cx="50%"
          cy="50%"
          outerRadius={100}
          label
          dataKey="value"
        >
          {pieData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>

       {/* Line Chart */}
       <h3>Line Chart - Sentiment Trend</h3>
      <LineChart
        width={600}
        height={300}
        data={lineData}
        margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="sentimentValue"
          stroke="#8884d8"
          activeDot={{ r: 8 }}
        />
      </LineChart>
      <div className="center-text">
        <p>Affiche une tendance basée sur la valeur du sentiment (1 pour positif, 0 pour neutre, -1 pour négatif).</p>
      </div>

      {/* Bar Chart */}
      <h3>Bar Chart - Sentiment Count</h3>
      <BarChart
        width={600}
        height={300}
        data={barData}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="sentiment" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill="#82ca9d" />
      </BarChart>
    </div>
  );
}

export default App;
