import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar 
} from 'recharts';
import API, { Bowler, Center, Pattern, Prediction, BowlerPerformance } from '../services/api';
import OilPatternVisualizer from './OilPatternVisualizer';

// Simple arrow indicators instead of lucide-react icons
const ArrowIndicators = {
  Up: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block text-green-600">
      <circle cx="12" cy="12" r="10" />
      <polyline points="16 12 12 8 8 12" />
      <line x1="12" y1="16" x2="12" y2="8" />
    </svg>
  ),
  Down: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block text-red-600">
      <circle cx="12" cy="12" r="10" />
      <polyline points="8 12 12 16 16 12" />
      <line x1="12" y1="8" x2="12" y2="16" />
    </svg>
  ),
  Neutral: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block text-gray-500">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
};

const PBAAnalysisApp: React.FC = () => {
  const [bowlers, setBowlers] = useState<Bowler[]>([]);
  const [centers, setCenters] = useState<Center[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [selectedCenter, setSelectedCenter] = useState<Center | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [selectedPatternLength, setSelectedPatternLength] = useState<string>('');
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

  // Fetch predictions with partial selections
  const fetchPredictions = async () => {
    // Require at least one selection (center or pattern or pattern length)
    if (selectedCenter || selectedPattern || (selectedPatternLength && selectedPatternLength.trim() !== '')) {
      setLoading(true);
      setError(null);
      try {
        const centerId = selectedCenter?.id || 0;
        const patternId = selectedPattern?.id || 0;
        
        // If using pattern length instead of pattern selection
        let effectivePatternId = patternId;
        if (!selectedPattern && selectedPatternLength && selectedPatternLength.trim() !== '') {
          // Find a pattern with matching length or create a temporary one
          const length = parseFloat(selectedPatternLength);
          if (!isNaN(length)) {
            const matchingPattern = patterns.find(p => Math.abs(p.length - length) < 0.5);
            if (matchingPattern) {
              effectivePatternId = matchingPattern.id;
            } else {
              // Could implement API call to handle custom length here
              // For now, we'll use a fallback approach
              console.log("Using custom pattern length:", length);
              // Find any pattern with similar length category
              if (length <= 36) {
                const shortPattern = patterns.find(p => p.category === 'Short');
                if (shortPattern) effectivePatternId = shortPattern.id;
              } else if (length <= 41) {
                const mediumPattern = patterns.find(p => p.category === 'Medium');
                if (mediumPattern) effectivePatternId = mediumPattern.id;
              } else if (length <= 47) {
                const longPattern = patterns.find(p => p.category === 'Long');
                if (longPattern) effectivePatternId = longPattern.id;
              } else {
                const extraLongPattern = patterns.find(p => p.category === 'Extra Long');
                if (extraLongPattern) effectivePatternId = extraLongPattern.id;
              }
            }
          }
        }
        
        // Get prediction data
        const predictionData = await API.getPredictions(centerId, effectivePatternId);
        console.log("Prediction data from API:", predictionData);
        
        // Get fresh bowler data directly from the API 
        const allBowlersData = await API.getBowlers();
        console.log("All bowlers data:", allBowlersData);
        
        // Combine the data correctly
        const enhancedPredictions = predictionData.map(prediction => {
          // Find this bowler in the complete bowlers data
          const bowlerData = allBowlersData.find(b => b.name === prediction.bowlerName);
          console.log(`Checking ${prediction.bowlerName}:`, bowlerData);
          
          // Get the actual average position from the bowlers data
          const actualAvgPosition = bowlerData?.avg_position || 0;
          
          // Keep the performance score from the backend
          const performanceScore = prediction.avgPosition || 0;
          
          // Calculate the position difference (compared to the actual average position)
          const positionDiff = actualAvgPosition - prediction.predictedPosition;
          
          return {
            ...prediction,
            avgPosition: performanceScore, // Keep the performance score
            actualAvgPosition,             // Add the actual average position  
            positionDiff                   // Add the correct position difference
          };
        });
        
        setPredictions(enhancedPredictions);
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
          
          // Round radar chart values to whole numbers
          if (performanceData?.patternRadar) {
            performanceData.patternRadar = performanceData.patternRadar.map(item => ({
              ...item,
              value: Math.round(item.value)
            }));
          }
          
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
    // Clear pattern length if a pattern is selected
    if (pattern) {
      setSelectedPatternLength('');
    }
  };

  // Handler for pattern length input
  const handlePatternLengthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedPatternLength(e.target.value);
    // Clear pattern selection if length is entered
    if (e.target.value.trim() !== '') {
      setSelectedPattern(null);
    }
  };

  // Handler for bowler selection
  const handleBowlerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const bowlerId = parseInt(e.target.value);
    const bowler = bowlers.find(b => b.id === bowlerId);
    setSelectedBowler(bowler || null);
  };

  // Helper function to get a description of the current selection
  const getSelectionDescription = () => {
    if (selectedCenter && selectedPattern) {
      return `${selectedPattern.name} pattern at ${selectedCenter.name}`;
    } else if (selectedCenter && selectedPatternLength && selectedPatternLength.trim() !== '') {
      return `${selectedPatternLength}ft pattern at ${selectedCenter.name}`;
    } else if (selectedCenter) {
      return `all patterns at ${selectedCenter.name}`;
    } else if (selectedPattern) {
      return `${selectedPattern.name} pattern at all centers`;
    } else if (selectedPatternLength && selectedPatternLength.trim() !== '') {
      return `${selectedPatternLength}ft pattern at all centers`;
    }
    return "using available data";
  };

  // Get position difference indicator
  const getPositionDiffIndicator = (diff: number | undefined) => {
    if (!diff || Math.abs(diff) < 0.5) {
      return <ArrowIndicators.Neutral />;
    } else if (diff > 0) {
      return <ArrowIndicators.Up />;
    } else {
      return <ArrowIndicators.Down />;
    }
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
                {center.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="border rounded p-4 shadow">
          <h2 className="text-xl font-semibold mb-2">Select Pattern</h2>
          <select 
            className="w-full p-2 border rounded mb-2" 
            onChange={handlePatternChange}
            value={selectedPattern?.id || ""}
            disabled={loading || patterns.length === 0 || selectedPatternLength.trim() !== ''}
          >
            <option value="">-- Select an Oil Pattern --</option>
            {patterns.map(pattern => (
              <option key={pattern.id} value={pattern.id}>
                {pattern.name} ({pattern.length}ft - {pattern.category})
              </option>
            ))}
          </select>
          
          <div className="mt-3">
            <h3 className="text-sm font-semibold mb-1">OR Enter Pattern Length</h3>
            <div className="flex items-center">
              <input
                type="number"
                min="30"
                max="50"
                step="1"
                className="w-full p-2 border rounded"
                placeholder="e.g., 42"
                value={selectedPatternLength}
                onChange={handlePatternLengthChange}
                disabled={loading || selectedPattern !== null}
              />
              <span className="ml-2">ft</span>
            </div>
          </div>
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
          disabled={loading || (!selectedCenter && !selectedPattern && selectedPatternLength.trim() === '')}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg disabled:opacity-50 text-lg"
        >
          {loading ? 'Generating...' : 'Generate Predictions'}
        </button>
        {(selectedCenter || selectedPattern || selectedPatternLength.trim() !== '') && (
          <p className="mt-2 text-gray-600">
            Generate predictions for {getSelectionDescription()}
          </p>
        )}
        {(!selectedCenter && !selectedPattern && selectedPatternLength.trim() === '') && (
          <p className="mt-2 text-gray-600">
            Please select at least a center, pattern, or pattern length to generate predictions
          </p>
        )}
      </div>

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
                  <th className="py-2 px-4 border-b text-left">Avg Position</th>
                  <th className="py-2 px-4 border-b text-left">vs Avg Position</th>
                  <th className="py-2 px-4 border-b text-left">Pattern Experience</th>
                  <th className="py-2 px-4 border-b text-left">Center Experience</th>
                  <th className="py-2 px-4 border-b text-left">Performance Score</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction, index) => (
                  <tr key={prediction.bowlerId} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="py-2 px-4 border-b">{index + 1}</td>
                    <td className="py-2 px-4 border-b font-medium">{prediction.bowlerName}</td>
                    <td className="py-2 px-4 border-b">{prediction.actualAvgPosition?.toFixed(1) || "N/A"}</td>
                    <td className="py-2 px-4 border-b">
                      {getPositionDiffIndicator(prediction.positionDiff)}
                      <span className={`ml-1 ${prediction.positionDiff ? 
                        (prediction.positionDiff > -0.5 ? 'text-green-600' : 
                        prediction.positionDiff < 0.5 ? 'text-red-600' : 
                        'text-gray-600') : 'text-gray-600'}`}
                      >
                        {prediction.positionDiff !== undefined ? 
                          (prediction.positionDiff >= 0 ? '+' : '') + prediction.positionDiff.toFixed(1) : '0.0'}
                      </span>
                    </td>
                    <td className="py-2 px-4 border-b">{prediction.patternExperience}</td>
                    <td className="py-2 px-4 border-b">{prediction.centerExperience}</td>
                    <td className="py-2 px-4 border-b">
                      <span className="text-blue-600">{prediction.avgPosition?.toFixed(1) || "N/A"}</span>
                      <span className="text-xs text-gray-500 ml-1">(0-100)</span>
                    </td>
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
                  <XAxis reversed dataKey="category" />
                  <YAxis yAxisId="left" orientation="left" reversed domain={[1,120]} />
                  <YAxis yAxisId="right" orientation="right" domain={[0,'dataMax + 2']} />
                  <Tooltip 
                    content={(props) => {
                      if (props.active && props.payload && props.payload.length) {
                        // Safe extraction with type checking
                        let avgPosition = "N/A";
                        let tournamentCount = "N/A";
      
                        props.payload.forEach(entry => {
                          if (entry.name === 'Avg Position' && entry.value !== undefined) {
                            avgPosition = typeof entry.value === 'number' 
                              ? entry.value.toFixed(2) 
                              : String(entry.value);
                          }
                          if (entry.name === 'Tournament Count' && entry.value !== undefined) {
                            tournamentCount = String(entry.value);
                          }
                        });
      
                        return (
                          <div className="bg-white p-2 border border-gray-300 shadow-md">
                            <p className="font-semibold">{props.label}</p>
                            <p className="text-indigo-700">Avg Position: {avgPosition}</p>
                            <p className="text-green-700">Tournament Count: {tournamentCount}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend 
                  payload={[
                      { value: 'Avg Position', type: 'square', color: '#8884d8' },
                      { value: 'Tournament Count', type: 'square', color: '#82ca9d' }
                    ]}
                  />
                  <Bar 
                    yAxisId="left"
                    dataKey="avgPosition" 
                    name="Avg Position" 
                    fill="#f5f5f5" 
                    stackId="stack"
                    minPointSize={1}
                    background={{ fill: "#8884d8" }}
                    maxBarSize={50}
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
                  <XAxis reversed dataKey="date" />
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
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tickFormatter={(value) => String(Math.round(value))} />
                  <Radar 
                    name="Performance" 
                    dataKey="value" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6} 
                  />
                  <Tooltip formatter={(value: any) => Math.round(value)} />
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
                  <XAxis reversed dataKey="category" />
                  <YAxis 
                    yAxisId="left" 
                    orientation="left"
                    domain={[0, (dataMax: number) => Math.ceil(dataMax / 1000) * 1000]}
                    tickFormatter={(value) => `$${value / 1000}k`}
                  />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white p-2 border border-gray-300 shadow-md">
                            <p className="font-semibold">{label}</p>
                            {payload.map((entry, index) => {
                              // Safely handle the value
                              let displayValue: string;
                              
                              // Check if value exists
                              if (entry.value === undefined || entry.value === null) {
                                displayValue = "N/A";
                              } else if (entry.dataKey === "avgEarnings" && typeof entry.value === 'number') {
                                // For earnings, format as currency
                                displayValue = `$${entry.value.toLocaleString('en-US', {
                                  minimumFractionDigits: 2,
                                  maximumFractionDigits: 2
                                })}`;
                              } else {
                                // For other data, convert to string safely
                                displayValue = String(entry.value);
                              }
                              
                              return (
                                <p key={`item-${index}`} style={{ color: entry.color }}>
                                  {entry.name}: {displayValue}
                                </p>
                              );
                            })}
                          </div>
                        );
                      }
                      return null;
                    }}
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
        <div className="mt-12 border-t pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded shadow">
              <h3 className="font-bold text-blue-800">Short Patterns ({"<"}36 feet)</h3>
            </div>
            <div className="bg-green-50 p-4 rounded shadow">
              <h3 className="font-bold text-green-800">Medium Patterns (37-41 feet)</h3>
            </div>   
            <div className="bg-amber-50 p-4 rounded shadow">
              <h3 className="font-bold text-amber-800">Long Patterns (42-47 feet)</h3>
            </div>   
            <div className="bg-red-50 p-4 rounded shadow">
              <h3 className="font-bold text-red-800">Extra Long Patterns (48+ feet)</h3>
            </div>
          </div>
        </div>
    </div>
  );
};

export default PBAAnalysisApp;