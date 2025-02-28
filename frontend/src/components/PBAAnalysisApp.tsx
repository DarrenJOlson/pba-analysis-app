import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar 
} from 'recharts';
import API, { Bowler, Center, Pattern, Prediction, BowlerPerformance } from '../services/api';
import OilPatternVisualizer from './OilPatternVisualizer';

const PBAAnalysisApp: React.FC = () => {
  const [bowlers, setBowlers] = useState<Bowler[]>([]);
  const [centers, setCenters] = useState<Center[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [selectedCenter, setSelectedCenter] = useState<Center | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [selectedBowler, setSelectedBowler] = useState<Bowler | null>(null);
  const [bowlerPerformance, setBowlerPerformance] = useState<BowlerPerformance | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch real data from API
        const bowlerData = await API.getBowlers();
        const centerData = await API.getCenters();
        const patternData = await API.getPatterns();
        
        setBowlers(bowlerData);
        setCenters(centerData);
        setPatterns(patternData);
      } catch (error) {
        console.error("Error fetching initial data:", error);
        setError("Failed to load initial data. Please check if the backend server is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // Modified: Fetch predictions with partial selections
  const fetchPredictions = async () => {
    // Require at least one selection (center or pattern)
    if (selectedCenter || selectedPattern) {
      setLoading(true);
      setError(null);
      try {
        const centerId = selectedCenter?.id || 0;
        const patternId = selectedPattern?.id || 0;
        
        const predictionData = await API.getPredictions(centerId, patternId);
        setPredictions(predictionData);
      } catch (error) {
        console.error("Error fetching predictions:", error);
        setError("Failed to load predictions. Please try again.");
      } finally {
        setLoading(false);
      }
    } else {
      setError("Please select at least a center or a pattern to generate predictions.");
    }
  };

  // Fetch bowler performance when a bowler is selected
  useEffect(() => {
    const fetchBowlerPerformance = async () => {
      if (selectedBowler) {
        setLoading(true);
        setError(null);
        try {
          const performanceData = await API.getBowlerPerformance(selectedBowler.id);
          setBowlerPerformance(performanceData);
        } catch (error) {
          console.error("Error fetching bowler performance:", error);
          setError("Failed to load bowler performance data. Please try again.");
        } finally {
          setLoading(false);
        }
      }
    };

    fetchBowlerPerformance();
  }, [selectedBowler]);

  // Handler for center selection
  const handleCenterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const centerId = parseInt(e.target.value);
    const center = centers.find(c => c.id === centerId);
    setSelectedCenter(center || null);
  };

  // Handler for pattern selection
  const handlePatternChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const patternId = parseInt(e.target.value);
    const pattern = patterns.find(p => p.id === patternId);
    setSelectedPattern(pattern || null);
  };

  // Handler for bowler selection
  const handleBowlerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const bowlerId = parseInt(e.target.value);
    const bowler = bowlers.find(b => b.id === bowlerId);
    setSelectedBowler(bowler || null);
  };

  // Handler for data collection
  const handleDataCollection = async () => {
    setLoading(true);
    setError(null);
    try {
      const currentYear = new Date().getFullYear();
      await API.collectData([currentYear]);
      // Reload all data after collection
      const bowlerData = await API.getBowlers();
      const centerData = await API.getCenters();
      const patternData = await API.getPatterns();
      
      setBowlers(bowlerData);
      setCenters(centerData);
      setPatterns(patternData);
      
      alert("Data collection completed successfully!");
    } catch (error) {
      console.error("Error collecting data:", error);
      setError("Failed to collect data. Please check the server logs.");
    } finally {
      setLoading(false);
    }
  };

  // Helper function to get a description of the current selection
  const getSelectionDescription = () => {
    if (selectedCenter && selectedPattern) {
      return `${selectedPattern.name} pattern at ${selectedCenter.name}`;
    } else if (selectedCenter) {
      return `all patterns at ${selectedCenter.name}`;
    } else if (selectedPattern) {
      return `${selectedPattern.name} pattern at all centers`;
    }
    return "using available data";
  };

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-center">PBA Tournament Analysis System</h1>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="mb-6 flex justify-end">
        <button 
          onClick={handleDataCollection}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Collect Latest Data'}
        </button>
      </div>
      
      {/* Selection Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="border rounded p-4 shadow">
          <h2 className="text-xl font-semibold mb-2">Select Center</h2>
          <select 
            className="w-full p-2 border rounded" 
            onChange={handleCenterChange}
            value={selectedCenter?.id || ""}
            disabled={loading || centers.length === 0}
          >
            <option value="">-- Select a Bowling Center --</option>
            {centers.map(center => (
              <option key={center.id} value={center.id}>
                {center.name} ({center.location})
              </option>
            ))}
          </select>
        </div>
        
        <div className="border rounded p-4 shadow">
          <h2 className="text-xl font-semibold mb-2">Select Pattern</h2>
          <select 
            className="w-full p-2 border rounded" 
            onChange={handlePatternChange}
            value={selectedPattern?.id || ""}
            disabled={loading || patterns.length === 0}
          >
            <option value="">-- Select an Oil Pattern --</option>
            {patterns.map(pattern => (
              <option key={pattern.id} value={pattern.id}>
                {pattern.name} ({pattern.length}ft - {pattern.category})
              </option>
            ))}
          </select>
        </div>
        
        <div className="border rounded p-4 shadow">
          <h2 className="text-xl font-semibold mb-2">Analyze Bowler</h2>
          <select 
            className="w-full p-2 border rounded" 
            onChange={handleBowlerChange}
            value={selectedBowler?.id || ""}
            disabled={loading || bowlers.length === 0}
          >
            <option value="">-- Select a Bowler --</option>
            {bowlers.map(bowler => (
              <option key={bowler.id} value={bowler.id}>
                {bowler.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      {/* Generate Predictions Button - Always visible */}
      <div className="mb-8 text-center">
        <button
          onClick={fetchPredictions}
          disabled={loading || (!selectedCenter && !selectedPattern)}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg disabled:opacity-50 text-lg"
        >
          {loading ? 'Generating...' : 'Generate Predictions'}
        </button>
        {(selectedCenter || selectedPattern) && (
          <p className="mt-2 text-gray-600">
            Generate predictions for {getSelectionDescription()}
          </p>
        )}
        {(!selectedCenter && !selectedPattern) && (
          <p className="mt-2 text-gray-600">
            Please select at least a center or a pattern to generate predictions
          </p>
        )}
      </div>
      
      {/* Pattern Visualization */}
      {selectedPattern && (
        <div className="mb-8">
          <OilPatternVisualizer 
            patternName={selectedPattern.name} 
            length={selectedPattern.length}
            volume={24} // Default oil volume
            ratio={3}   // Default ratio
          />
        </div>
      )}
      
      {/* Predictions Section */}
      {predictions.length > 0 && (
        <div className="mb-8 border rounded p-4 shadow">
          <h2 className="text-2xl font-semibold mb-4">
            Predicted Performance {getSelectionDescription()}
          </h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead className="bg-gray-100">
                <tr>
                  <th className="py-2 px-4 border-b text-left">Rank</th>
                  <th className="py-2 px-4 border-b text-left">Bowler</th>
                  <th className="py-2 px-4 border-b text-left">Predicted Position</th>
                  <th className="py-2 px-4 border-b text-left">Pattern Experience</th>
                  <th className="py-2 px-4 border-b text-left">Center Experience</th>
                  <th className="py-2 px-4 border-b text-left">Win Percentage</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction, index) => (
                  <tr key={prediction.bowlerId} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="py-2 px-4 border-b">{index + 1}</td>
                    <td className="py-2 px-4 border-b font-medium">{prediction.bowlerName}</td>
                    <td className="py-2 px-4 border-b">{prediction.predictedPosition.toFixed(1)}</td>
                    <td className="py-2 px-4 border-b">{prediction.patternExperience}</td>
                    <td className="py-2 px-4 border-b">{prediction.centerExperience}</td>
                    <td className="py-2 px-4 border-b">{prediction.winPercentage.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-6">
            <h3 className="text-xl font-semibold mb-2">Predicted Positions Visualization</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={predictions}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bowlerName" />
                <YAxis reversed/>
                <Tooltip formatter={(value: any) => value.toFixed(1)} />
                <Legend />
                <Bar 
                  dataKey="predictedPosition" 
                  name="Predicted Position" 
                  fill="#8884d8" 
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {/* Bowler Analysis Section */}
      {selectedBowler && bowlerPerformance && (
        <div className="border rounded p-4 shadow">
          <h2 className="text-2xl font-semibold mb-4">
            {selectedBowler.name} - Performance Analysis
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pattern Performance */}
            <div className="border rounded p-4">
              <h3 className="text-xl font-semibold mb-2">Performance by Pattern</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={bowlerPerformance.byPattern}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis yAxisId="left" orientation="left" />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 'dataMax + 2']} />
                  <Tooltip />
                  <Legend />
                  <Bar 
                    yAxisId="left"
                    dataKey="avgPosition" 
                    name="Avg Position" 
                    fill="#8884d8" 
                  />
                  <Bar 
                    yAxisId="right"
                    dataKey="tournamentCount" 
                    name="Tournament Count" 
                    fill="#82ca9d" 
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            {/* Recent Performance Trend */}
            <div className="border rounded p-4">
              <h3 className="text-xl font-semibold mb-2">Recent Performance Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={bowlerPerformance.recentTrend}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis reversed domain={[1, 'dataMax + 2']} />
                  <Tooltip 
                    formatter={(value: any, name: any) => [
                      value, 
                      name === "position" ? "Position" : name
                    ]}
                    labelFormatter={(label: any) => `Tournament: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="position" 
                    name="Position" 
                    stroke="#8884d8" 
                    activeDot={{ r: 8 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            {/* Skill Radar */}
            <div className="border rounded p-4">
              <h3 className="text-xl font-semibold mb-2">Skill Profile</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart 
                  cx="50%" 
                  cy="50%" 
                  outerRadius="80%" 
                  data={bowlerPerformance.patternRadar}
                >
                  <PolarGrid />
                  <PolarAngleAxis dataKey="attribute" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar 
                    name="Performance" 
                    dataKey="value" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6} 
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            
            {/* Pattern Experience Distribution */}
            <div className="border rounded p-4">
              <h3 className="text-xl font-semibold mb-2">Pattern Experience vs. Earnings</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={bowlerPerformance.byPattern}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis 
                    yAxisId="left" 
                    orientation="left"
                    domain={[0, 'dataMax + 5000']}
                    tickFormatter={(value) => `$${value / 1000}k`}
                  />
                  <Tooltip 
                    formatter={(value: any, name: any) => [
                      name === "avgEarnings" ? `$${value.toLocaleString()}` : value,
                      name === "avgEarnings" ? "Avg Earnings" : name
                    ]}
                  />
                  <Legend />
                  <Bar 
                    yAxisId="left"
                    dataKey="avgEarnings" 
                    name="Avg Earnings" 
                    fill="#ffc658" 
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
      
      {/* Loading indicator */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded shadow text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2">Loading data...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PBAAnalysisApp;