import React, { useState, useEffect } from 'react';
import { 
    Activity, Server, Database, AlertCircle 
} from 'lucide-react';
import { scraping } from '../services/api';

const SystemMonitor = () => {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const data = await scraping.getSystemStatus();
                setMetrics(data.metrics);
                setError(null);
            } catch (err) {
                setError('Failed to fetch system metrics');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="animate-pulse flex space-x-4">
                <div className="h-12 w-12 bg-gray-200 rounded"></div>
                <div className="flex-1 space-y-4">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-red-600 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                {error}
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">System Status</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Performance Metrics */}
                <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-blue-600" />
                        <span className="font-medium">Performance</span>
                    </div>
                    <div className="mt-2 space-y-1">
                        <div className="text-sm">
                            Success Rate: {metrics.success_rate.toFixed(1)}%
                        </div>
                        <div className="text-sm">
                            Response Time: {metrics.avg_response_time.toFixed(0)}ms
                        </div>
                    </div>
                </div>

                {/* Resource Usage */}
                <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2">
                        <Server className="h-5 w-5 text-green-600" />
                        <span className="font-medium">Resources</span>
                    </div>
                    <div className="mt-2 space-y-1">
                        <div className="text-sm">
                            CPU: {metrics.cpu_usage.toFixed(1)}%
                        </div>
                        <div className="text-sm">
                            Memory: {metrics.memory_usage.toFixed(1)}%
                        </div>
                    </div>
                </div>

                {/* Scraping Stats */}
                <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-2">
                        <Database className="h-5 w-5 text-purple-600" />
                        <span className="font-medium">Activity</span>
                    </div>
                    <div className="mt-2 space-y-1">
                        <div className="text-sm">
                            Active Jobs: {metrics.active_jobs}
                        </div>
                        <div className="text-sm">
                            Items/min: {metrics.items_per_minute.toFixed(1)}
                        </div>
                    </div>
                </div>

                {/* Error Stats */}
                <div className="p-4 bg-red-50 rounded-lg">
                    <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <span className="font-medium">Errors</span>
                    </div>
                    <div className="mt-2 space-y-1">
                        <div className="text-sm">
                            Count: {metrics.errors_count}
                        </div>
                        <div className="text-sm">
                            Bandwidth: {metrics.bandwidth_usage.toFixed(2)}MB/s
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemMonitor;