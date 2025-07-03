"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Loader2 } from "lucide-react"

// ==================== 数据接口类型定义 ====================
interface TimeSeriesData {
  time: string
  probability: number
  timestamp: number
}

interface LatestDataPoint {
  temperature: number
  faultProbability: number
  timestamp: string
}

interface DashboardData {
  timeSeries: TimeSeriesData[]
  latestData: LatestDataPoint
  availableWaterjets: string[]
  availableDates: string[]
}

// ==================== API接口预留区域 ====================

/**
 * 获取仪表板数据的API接口
 * @param waterjet 水刀设备ID
 * @param date 选择的日期 (格式: YYYY-MM-DD)
 * @returns Promise<DashboardData>
 *
 * 后端API端点建议: GET /api/fault-data?waterjet={waterjet}&date={date}
 *
 * 预期返回数据格式:
 * {
 *   "timeSeries": [
 *     {
 *       "time": "Thu 15 02:00",
 *       "probability": 0.85,
 *       "timestamp": 1715742000000
 *     }
 *   ],
 *   "latestData": {
 *     "temperature": 29.56,
 *     "faultProbability": 18.99,
 *     "timestamp": "23:45"
 *   },
 *   "availableWaterjets": ["WJ-001", "WJ-002"],
 *   "availableDates": ["2025-05-15", "2025-05-14"]
 * }
 */
const fetchDashboardData = async (waterjet: string, date: string): Promise<DashboardData> => {
  try {
    // TODO: 替换为实际的API调用
    const response = await fetch(`/api/fault-data?waterjet=${waterjet}&date=${date}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error("Failed to fetch dashboard data:", error)
    throw error
  }
}

/**
 * 获取可用水刀设备列表的API接口
 * @returns Promise<string[]>
 *
 * 后端API端点建议: GET /api/waterjets
 *
 * 预期返回数据格式:
 * ["WJ-001", "WJ-002", "WJ-003", "WJ-004"]
 */
const fetchAvailableWaterjets = async (): Promise<string[]> => {
  try {
    // TODO: 替换为实际的API调用
    const response = await fetch("/api/waterjets")

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error("Failed to fetch waterjets:", error)
    throw error
  }
}

/**
 * 获取可用日期列表的API接口
 * @param waterjet 水刀设备ID
 * @returns Promise<string[]>
 *
 * 后端API端点建议: GET /api/available-dates?waterjet={waterjet}
 *
 * 预期返回数据格式:
 * ["2025-05-15", "2025-05-14", "2025-05-13", "2025-05-12"]
 */
const fetchAvailableDates = async (waterjet: string): Promise<string[]> => {
  try {
    // TODO: 替换为实际的API调用
    const response = await fetch(`/api/available-dates?waterjet=${waterjet}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error("Failed to fetch available dates:", error)
    throw error
  }
}

// ==================== 主组件 ====================

export default function FaultMonitoringDashboard() {
  // 状态管理
  const [selectedWaterjet, setSelectedWaterjet] = useState<string>("")
  const [selectedDate, setSelectedDate] = useState<string>("")
  const [timeRange, setTimeRange] = useState([0, 1435]) // 0-1435 minutes (00:00-23:45)

  // 数据状态
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [filteredData, setFilteredData] = useState<TimeSeriesData[]>([])
  const [availableWaterjets, setAvailableWaterjets] = useState<string[]>([])
  const [availableDates, setAvailableDates] = useState<string[]>([])

  // 加载和错误状态
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 初始化加载可用水刀设备
  useEffect(() => {
    const initializeWaterjets = async () => {
      try {
        setIsInitialLoading(true)
        const waterjets = await fetchAvailableWaterjets()
        setAvailableWaterjets(waterjets)

        if (waterjets.length > 0) {
          setSelectedWaterjet(waterjets[0])
        }
      } catch (err) {
        setError("Failed to load waterjet devices")
      } finally {
        setIsInitialLoading(false)
      }
    }

    initializeWaterjets()
  }, [])

  // 当选择的水刀改变时，加载可用日期
  useEffect(() => {
    if (!selectedWaterjet) return

    const loadAvailableDates = async () => {
      try {
        const dates = await fetchAvailableDates(selectedWaterjet)
        setAvailableDates(dates)

        if (dates.length > 0) {
          setSelectedDate(dates[0])
        }
      } catch (err) {
        setError("Failed to load available dates")
      }
    }

    loadAvailableDates()
  }, [selectedWaterjet])

  // 当参数改变时重新获取仪表板数据
  useEffect(() => {
    if (!selectedWaterjet || !selectedDate) return

    const loadDashboardData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await fetchDashboardData(selectedWaterjet, selectedDate)
        setDashboardData(data)
      } catch (err) {
        setError("Failed to load dashboard data")
        setDashboardData(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadDashboardData()
  }, [selectedWaterjet, selectedDate])

  // 过滤时间范围内的数据
  useEffect(() => {
    if (!dashboardData?.timeSeries) {
      setFilteredData([])
      return
    }

    const startMinutes = timeRange[0]
    const endMinutes = timeRange[1]

    const filtered = dashboardData.timeSeries.filter((item) => {
      const itemDate = new Date(item.timestamp)
      const itemMinutes = itemDate.getHours() * 60 + itemDate.getMinutes()
      return itemMinutes >= startMinutes && itemMinutes <= endMinutes
    })

    setFilteredData(filtered)
  }, [dashboardData?.timeSeries, timeRange])

  // 工具函数
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}`
  }

  // 图表工具提示自定义
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="text-sm font-medium">{`时间: ${label}`}</p>
          <p className="text-sm text-blue-600">{`故障概率: ${(payload[0].value * 100).toFixed(2)}%`}</p>
        </div>
      )
    }
    return null
  }

  // 初始加载状态
  if (isInitialLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading dashboard...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左侧参数选择面板 */}
          <div className="lg:col-span-1">
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="text-lg font-medium">选择参数 (Select Parameters)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 选择水刀 */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">选择水刀 (Select Waterjet)</label>
                  <Select value={selectedWaterjet} onValueChange={setSelectedWaterjet}>
                    <SelectTrigger>
                      <SelectValue placeholder="请选择水刀设备" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableWaterjets.map((waterjet) => (
                        <SelectItem key={waterjet} value={waterjet}>
                          {waterjet}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* 选择日期 */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">选择日期 (Select Date)</label>
                  <Select value={selectedDate} onValueChange={setSelectedDate} disabled={!selectedWaterjet}>
                    <SelectTrigger>
                      <SelectValue placeholder="请选择日期" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableDates.map((date) => (
                        <SelectItem key={date} value={date}>
                          {date}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* 时间范围选择 */}
                <div className="space-y-4">
                  <label className="text-sm font-medium text-gray-700">选择时间范围 (Select Time Range)</label>
                  <div className="px-2">
                    <Slider
                      value={timeRange}
                      onValueChange={setTimeRange}
                      max={1435}
                      min={0}
                      step={15}
                      className="w-full"
                      disabled={!selectedWaterjet || !selectedDate}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                      <span>{formatTime(timeRange[0])}</span>
                      <span>{formatTime(timeRange[1])}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 右侧主要内容区域 */}
          <div className="lg:col-span-3 space-y-6">
            {/* 图表区域 */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-xl font-semibold">
                  故障概率时间序列 (Fault Probability Time Series)
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    Deploy
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-80 w-full">
                  {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span>Loading chart data...</span>
                      </div>
                    </div>
                  ) : filteredData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="time" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
                        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} tickFormatter={(value) => value.toFixed(1)} />
                        <Tooltip content={<CustomTooltip />} />
                        <Line
                          type="monotone"
                          dataKey="probability"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4, fill: "#2563eb" }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <p>No data available for the selected parameters</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 最新数据点显示 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">
                  最新数据点 (Latest Data Point
                  {dashboardData?.latestData?.timestamp ? ` at ${dashboardData.latestData.timestamp}` : ""}):
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Loading latest data...</span>
                    </div>
                  </div>
                ) : dashboardData?.latestData ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">温度 (Temperature)</p>
                      <p className="text-3xl font-bold text-gray-900">{dashboardData.latestData.temperature}°C</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">故障概率 (Fault Probability)</p>
                      <p className="text-3xl font-bold text-gray-900">{dashboardData.latestData.faultProbability}%</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-500">
                    <p>No latest data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
