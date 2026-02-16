"""
Analyzer Service

Handles power flow analysis, stability assessment, metrics calculation,
report generation, and Core Dump analysis.
"""

import uuid
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.exc import IntegrityError

from utils.database import SessionLocal
from utils.logger import setup_logger
from utils.errors import (
    AnalysisError, ValidationError, DatabaseError
)
from utils.metrics import (
    time_database_query
)
from models.analysis_result import AnalysisResult
from utils.validators import (
    PowerFlowAnalysisRequest, StabilityAnalysisRequest,
    MetricsRequest, ReportRequest
)

logger = setup_logger(__name__)


class Analyzer:
    """Handles power system analysis, metrics calculation, and report generation"""
    
    # Analysis timeout limits (in seconds)
    POWER_FLOW_TIMEOUT = 5
    STABILITY_TIMEOUT = 10
    METRICS_TIMEOUT = 2
    REPORT_TIMEOUT = 30
    
    def __init__(self):
        """Initialize analyzer service"""
        self.session = SessionLocal()
    
    def __del__(self):
        """Cleanup session"""
        if self.session:
            self.session.close()
    
    @time_database_query("power_flow_analysis")
    def analyze_power_flow(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute power flow analysis on the system
        
        Performs power flow calculation using pandapower library to determine
        voltage profiles, power flows, and convergence status.
        
        Args:
            system_state: Dictionary containing system state with device parameters
                         (power generation, consumption, storage state)
        
        Returns:
            Dictionary with analysis results including:
            - analysis_id: Unique analysis identifier
            - status: "completed" or "failed"
            - voltage_profiles: Voltage at each bus
            - power_flows: Power flow on each line
            - convergence_status: Whether analysis converged
            - execution_time_ms: Time taken for analysis
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If analysis fails or times out
            ValidationError: If system_state is invalid
        """
        analysis_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate input
            if not isinstance(system_state, dict):
                raise ValidationError(
                    "system_state must be a dictionary",
                    details={"system_state": system_state}
                )
            
            if not system_state:
                raise ValidationError(
                    "system_state cannot be empty",
                    details={"system_state": system_state}
                )
            
            logger.info(
                f"Starting power flow analysis: {analysis_id}",
                extra={"analysis_id": analysis_id}
            )
            
            # Execute power flow analysis
            result_data = self._execute_power_flow_calculation(system_state)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Check timeout
            if execution_time_ms > self.POWER_FLOW_TIMEOUT * 1000:
                raise AnalysisError(
                    f"Power flow analysis exceeded timeout ({self.POWER_FLOW_TIMEOUT}s)",
                    details={"execution_time_ms": execution_time_ms}
                )
            
            # Persist results
            analysis_result = AnalysisResult(
                id=analysis_id,
                analysis_type="power_flow",
                system_state=system_state,
                result_data=result_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Power flow analysis completed: {analysis_id}",
                extra={
                    "analysis_id": analysis_id,
                    "execution_time_ms": execution_time_ms,
                    "convergence": result_data.get("convergence_status", False)
                }
            )
            
            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "voltage_profiles": result_data.get("voltage_profiles", {}),
                "power_flows": result_data.get("power_flows", {}),
                "convergence_status": result_data.get("convergence_status", False),
                "execution_time_ms": execution_time_ms
            }
        
        except AnalysisError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Power flow analysis failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"analysis_id": analysis_id, "error": str(e)},
                exc_info=True
            )
            
            # Persist failed analysis
            try:
                analysis_result = AnalysisResult(
                    id=analysis_id,
                    analysis_type="power_flow",
                    system_state=system_state,
                    result_data={},
                    status="failed",
                    error_message=error_msg,
                    execution_time_ms=execution_time_ms
                )
                self.session.add(analysis_result)
                self.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to persist analysis error: {str(db_error)}")
            
            raise AnalysisError(error_msg, details={"analysis_id": analysis_id})
    
    @time_database_query("stability_analysis")
    def analyze_stability(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute stability analysis on the system
        
        Assesses system stability by evaluating frequency deviation,
        voltage stability, and transient stability metrics.
        
        Args:
            system_state: Dictionary containing system state parameters
        
        Returns:
            Dictionary with stability analysis results including:
            - analysis_id: Unique analysis identifier
            - status: "completed" or "failed"
            - frequency_deviation: Frequency deviation in Hz
            - voltage_stability: Voltage stability assessment
            - transient_stability: Transient stability assessment
            - risk_level: "low", "medium", or "high"
            - execution_time_ms: Time taken for analysis
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If analysis fails or times out
            ValidationError: If system_state is invalid
        """
        analysis_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate input
            if not isinstance(system_state, dict):
                raise ValidationError(
                    "system_state must be a dictionary",
                    details={"system_state": system_state}
                )
            
            logger.info(
                f"Starting stability analysis: {analysis_id}",
                extra={"analysis_id": analysis_id}
            )
            
            # Execute stability analysis
            result_data = self._execute_stability_calculation(system_state)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Check timeout
            if execution_time_ms > self.STABILITY_TIMEOUT * 1000:
                raise AnalysisError(
                    f"Stability analysis exceeded timeout ({self.STABILITY_TIMEOUT}s)",
                    details={"execution_time_ms": execution_time_ms}
                )
            
            # Persist results
            analysis_result = AnalysisResult(
                id=analysis_id,
                analysis_type="stability",
                system_state=system_state,
                result_data=result_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Stability analysis completed: {analysis_id}",
                extra={
                    "analysis_id": analysis_id,
                    "execution_time_ms": execution_time_ms,
                    "risk_level": result_data.get("risk_level", "unknown")
                }
            )
            
            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "frequency_deviation": result_data.get("frequency_deviation", 0.0),
                "voltage_stability": result_data.get("voltage_stability", {}),
                "transient_stability": result_data.get("transient_stability", {}),
                "risk_level": result_data.get("risk_level", "low"),
                "execution_time_ms": execution_time_ms
            }
        
        except AnalysisError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Stability analysis failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"analysis_id": analysis_id, "error": str(e)},
                exc_info=True
            )
            
            # Persist failed analysis
            try:
                analysis_result = AnalysisResult(
                    id=analysis_id,
                    analysis_type="stability",
                    system_state=system_state,
                    result_data={},
                    status="failed",
                    error_message=error_msg,
                    execution_time_ms=execution_time_ms
                )
                self.session.add(analysis_result)
                self.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to persist analysis error: {str(db_error)}")
            
            raise AnalysisError(error_msg, details={"analysis_id": analysis_id})
    
    @time_database_query("metrics_calculation")
    def calculate_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "hourly"
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for the system
        
        Computes efficiency metrics, response time metrics, and dispatch
        success rates over a specified time period.
        
        Args:
            start_time: Start time for metrics calculation
            end_time: End time for metrics calculation
            aggregation: Aggregation level ("hourly", "daily", "monthly")
        
        Returns:
            Dictionary with metrics results including:
            - metrics_id: Unique metrics identifier
            - status: "completed" or "failed"
            - efficiency: System efficiency percentage
            - response_time_ms: Average response time
            - dispatch_success_rate: Success rate percentage
            - aggregation: Aggregation level used
            - execution_time_ms: Time taken for calculation
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If calculation fails or times out
            ValidationError: If parameters are invalid
        """
        metrics_id = str(uuid.uuid4())
        calc_start_time = time.time()
        
        try:
            # Validate input
            if not isinstance(start_time, datetime):
                raise ValidationError(
                    "start_time must be a datetime object",
                    details={"start_time": str(start_time)}
                )
            
            if not isinstance(end_time, datetime):
                raise ValidationError(
                    "end_time must be a datetime object",
                    details={"end_time": str(end_time)}
                )
            
            if start_time >= end_time:
                raise ValidationError(
                    "start_time must be before end_time",
                    details={"start_time": str(start_time), "end_time": str(end_time)}
                )
            
            if aggregation not in ["hourly", "daily", "monthly"]:
                raise ValidationError(
                    "aggregation must be 'hourly', 'daily', or 'monthly'",
                    details={"aggregation": aggregation}
                )
            
            logger.info(
                f"Starting metrics calculation: {metrics_id}",
                extra={
                    "metrics_id": metrics_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "aggregation": aggregation
                }
            )
            
            # Calculate metrics
            result_data = self._calculate_metrics_data(
                start_time, end_time, aggregation
            )
            
            execution_time_ms = int((time.time() - calc_start_time) * 1000)
            
            # Check timeout
            if execution_time_ms > self.METRICS_TIMEOUT * 1000:
                raise AnalysisError(
                    f"Metrics calculation exceeded timeout ({self.METRICS_TIMEOUT}s)",
                    details={"execution_time_ms": execution_time_ms}
                )
            
            # Persist results
            system_state = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "aggregation": aggregation
            }
            
            analysis_result = AnalysisResult(
                id=metrics_id,
                analysis_type="metrics",
                system_state=system_state,
                result_data=result_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Metrics calculation completed: {metrics_id}",
                extra={
                    "metrics_id": metrics_id,
                    "execution_time_ms": execution_time_ms,
                    "efficiency": result_data.get("efficiency", 0.0)
                }
            )
            
            return {
                "metrics_id": metrics_id,
                "status": "completed",
                "efficiency": result_data.get("efficiency", 0.0),
                "response_time_ms": result_data.get("response_time_ms", 0.0),
                "dispatch_success_rate": result_data.get("dispatch_success_rate", 0.0),
                "aggregation": aggregation,
                "execution_time_ms": execution_time_ms
            }
        
        except AnalysisError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - calc_start_time) * 1000)
            error_msg = f"Metrics calculation failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"metrics_id": metrics_id, "error": str(e)},
                exc_info=True
            )
            
            raise AnalysisError(error_msg, details={"metrics_id": metrics_id})
    
    @time_database_query("report_generation")
    def generate_report(
        self,
        report_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis reports
        
        Creates performance, vulnerability, or analysis reports with
        relevant data, metrics, and recommendations.
        
        Args:
            report_type: Type of report ("performance", "vulnerability", "analysis")
            filters: Optional filters for report generation
        
        Returns:
            Dictionary with report results including:
            - report_id: Unique report identifier
            - status: "completed" or "failed"
            - report_type: Type of report generated
            - report_data: Report content in JSON format
            - execution_time_ms: Time taken for generation
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If report generation fails or times out
            ValidationError: If parameters are invalid
        """
        report_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate input
            valid_types = ["performance", "vulnerability", "analysis"]
            if report_type not in valid_types:
                raise ValidationError(
                    f"report_type must be one of {valid_types}",
                    details={"report_type": report_type}
                )
            
            if filters is None:
                filters = {}
            
            logger.info(
                f"Starting report generation: {report_id}",
                extra={
                    "report_id": report_id,
                    "report_type": report_type
                }
            )
            
            # Generate report
            report_data = self._generate_report_data(report_type, filters)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Check timeout
            if execution_time_ms > self.REPORT_TIMEOUT * 1000:
                raise AnalysisError(
                    f"Report generation exceeded timeout ({self.REPORT_TIMEOUT}s)",
                    details={"execution_time_ms": execution_time_ms}
                )
            
            # Persist results
            system_state = {
                "report_type": report_type,
                "filters": filters
            }
            
            analysis_result = AnalysisResult(
                id=report_id,
                analysis_type="report",
                system_state=system_state,
                result_data=report_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Report generation completed: {report_id}",
                extra={
                    "report_id": report_id,
                    "report_type": report_type,
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return {
                "report_id": report_id,
                "status": "completed",
                "report_type": report_type,
                "report_data": report_data,
                "execution_time_ms": execution_time_ms
            }
        
        except AnalysisError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Report generation failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"report_id": report_id, "error": str(e)},
                exc_info=True
            )
            
            raise AnalysisError(error_msg, details={"report_id": report_id})
    
    @time_database_query("core_dump_analysis")
    def analyze_core_dump(
        self,
        core_dump_data: bytes
    ) -> Dict[str, Any]:
        """
        Analyze Core Dump files for vulnerability assessment
        
        Parses Core Dump files to extract crash information including
        crash address, call stack, and register state.
        
        Args:
            core_dump_data: Binary Core Dump file data
        
        Returns:
            Dictionary with Core Dump analysis results including:
            - dump_id: Unique dump analysis identifier
            - status: "completed" or "failed"
            - crash_address: Address where crash occurred
            - call_stack: Call stack at crash time
            - register_state: Register values at crash time
            - execution_time_ms: Time taken for analysis
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If Core Dump analysis fails
            ValidationError: If Core Dump data is invalid
        """
        dump_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate input
            if not isinstance(core_dump_data, bytes):
                raise ValidationError(
                    "core_dump_data must be bytes",
                    details={"data_type": type(core_dump_data).__name__}
                )
            
            if len(core_dump_data) == 0:
                raise ValidationError(
                    "core_dump_data cannot be empty",
                    details={"data_length": 0}
                )
            
            logger.info(
                f"Starting Core Dump analysis: {dump_id}",
                extra={
                    "dump_id": dump_id,
                    "data_size": len(core_dump_data)
                }
            )
            
            # Parse Core Dump
            result_data = self._parse_core_dump(core_dump_data)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Persist results
            system_state = {
                "dump_size": len(core_dump_data),
                "analysis_time": datetime.utcnow().isoformat()
            }
            
            analysis_result = AnalysisResult(
                id=dump_id,
                analysis_type="core_dump",
                system_state=system_state,
                result_data=result_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Core Dump analysis completed: {dump_id}",
                extra={
                    "dump_id": dump_id,
                    "execution_time_ms": execution_time_ms,
                    "crash_address": result_data.get("crash_address", "unknown")
                }
            )
            
            return {
                "dump_id": dump_id,
                "status": "completed",
                "crash_address": result_data.get("crash_address", "0x0"),
                "call_stack": result_data.get("call_stack", []),
                "register_state": result_data.get("register_state", {}),
                "execution_time_ms": execution_time_ms
            }
        
        except ValidationError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Core Dump analysis failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"dump_id": dump_id, "error": str(e)},
                exc_info=True
            )
            
            raise AnalysisError(error_msg, details={"dump_id": dump_id})
    
    @time_database_query("vulnerability_report_generation")
    def generate_vulnerability_report(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate vulnerability reports from Core Dump analysis
        
        Compiles vulnerability findings from Core Dump analyses with
        crash details, affected protocols, severity levels, and recommendations.
        
        Args:
            filters: Optional filters for report generation
        
        Returns:
            Dictionary with vulnerability report results including:
            - report_id: Unique report identifier
            - status: "completed" or "failed"
            - vulnerabilities: List of identified vulnerabilities
            - severity_summary: Summary of severity levels
            - recommendations: Remediation recommendations
            - execution_time_ms: Time taken for generation
            - error_message: Error details if failed
        
        Raises:
            AnalysisError: If report generation fails or times out
        """
        report_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            if filters is None:
                filters = {}
            
            logger.info(
                f"Starting vulnerability report generation: {report_id}",
                extra={"report_id": report_id}
            )
            
            # Generate vulnerability report
            report_data = self._generate_vulnerability_report_data(filters)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Check timeout
            if execution_time_ms > self.REPORT_TIMEOUT * 1000:
                raise AnalysisError(
                    f"Vulnerability report generation exceeded timeout ({self.REPORT_TIMEOUT}s)",
                    details={"execution_time_ms": execution_time_ms}
                )
            
            # Persist results
            system_state = {
                "report_type": "vulnerability",
                "filters": filters
            }
            
            analysis_result = AnalysisResult(
                id=report_id,
                analysis_type="vulnerability_report",
                system_state=system_state,
                result_data=report_data,
                status="completed",
                execution_time_ms=execution_time_ms
            )
            
            self.session.add(analysis_result)
            self.session.commit()
            
            logger.info(
                f"Vulnerability report generation completed: {report_id}",
                extra={
                    "report_id": report_id,
                    "execution_time_ms": execution_time_ms,
                    "vulnerability_count": len(report_data.get("vulnerabilities", []))
                }
            )
            
            return {
                "report_id": report_id,
                "status": "completed",
                "vulnerabilities": report_data.get("vulnerabilities", []),
                "severity_summary": report_data.get("severity_summary", {}),
                "recommendations": report_data.get("recommendations", []),
                "execution_time_ms": execution_time_ms
            }
        
        except AnalysisError:
            raise
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Vulnerability report generation failed: {str(e)}"
            
            logger.error(
                error_msg,
                extra={"report_id": report_id, "error": str(e)},
                exc_info=True
            )
            
            raise AnalysisError(error_msg, details={"report_id": report_id})
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _execute_power_flow_calculation(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute power flow calculation using pandapower
        
        Args:
            system_state: System state parameters containing:
                - buses: List of bus definitions with voltage, type, etc.
                - lines: List of line definitions with from_bus, to_bus, impedance
                - generators: List of generator definitions with power output
                - loads: List of load definitions with power consumption
        
        Returns:
            Dictionary with power flow results including:
            - voltage_profiles: Voltage magnitude at each bus
            - power_flows: Power flow on each line
            - convergence_status: Whether analysis converged
        
        Raises:
            AnalysisError: If power flow calculation fails
        """
        try:
            import pandapower as pp
            
            # Create pandapower network
            net = pp.create_empty_network()
            
            # Add buses from system state
            buses = system_state.get("buses", [])
            if not buses:
                raise AnalysisError(
                    "No buses defined in system state",
                    details={"buses": buses}
                )
            
            bus_mapping = {}  # Map bus IDs to pandapower bus indices
            for bus_data in buses:
                bus_id = bus_data.get("id")
                if not bus_id:
                    raise AnalysisError(
                        "Bus missing required 'id' field",
                        details={"bus_data": bus_data}
                    )
                
                vn_kv = bus_data.get("voltage_nominal", 110.0)
                bus_idx = pp.create_bus(
                    net,
                    vn_kv=vn_kv,
                    name=bus_id
                )
                bus_mapping[bus_id] = bus_idx
            
            # Add lines from system state
            lines = system_state.get("lines", [])
            for line_data in lines:
                from_bus_id = line_data.get("from_bus")
                to_bus_id = line_data.get("to_bus")
                
                if not from_bus_id or not to_bus_id:
                    raise AnalysisError(
                        "Line missing required 'from_bus' or 'to_bus' field",
                        details={"line_data": line_data}
                    )
                
                if from_bus_id not in bus_mapping or to_bus_id not in bus_mapping:
                    raise AnalysisError(
                        "Line references undefined bus",
                        details={
                            "from_bus": from_bus_id,
                            "to_bus": to_bus_id,
                            "available_buses": list(bus_mapping.keys())
                        }
                    )
                
                # Get line parameters
                length_km = line_data.get("length", 1.0)
                
                # Use standard type if provided, otherwise use a default
                std_type = line_data.get("std_type", "24-AL1/4-ST1A 10.0")
                
                try:
                    pp.create_line(
                        net,
                        from_bus=bus_mapping[from_bus_id],
                        to_bus=bus_mapping[to_bus_id],
                        length_km=length_km,
                        std_type=std_type,
                        name=line_data.get("id", f"{from_bus_id}-{to_bus_id}")
                    )
                except Exception:
                    # If standard type doesn't exist, create with basic parameters
                    pp.create_line_from_parameters(
                        net,
                        from_bus=bus_mapping[from_bus_id],
                        to_bus=bus_mapping[to_bus_id],
                        length_km=length_km,
                        r_ohm_per_km=0.05,
                        x_ohm_per_km=0.1,
                        c_nf_per_km=0.0,
                        max_i_ka=1.0,
                        name=line_data.get("id", f"{from_bus_id}-{to_bus_id}")
                    )
            
            # Add generators from system state
            generators = system_state.get("generators", [])
            for i, gen_data in enumerate(generators):
                bus_id = gen_data.get("bus")
                if not bus_id or bus_id not in bus_mapping:
                    raise AnalysisError(
                        "Generator references undefined bus",
                        details={"bus": bus_id}
                    )
                
                p_mw = gen_data.get("power", 0.0)
                vm_pu = gen_data.get("voltage", 1.0)
                
                # First generator is slack bus
                is_slack = (i == 0)
                
                pp.create_gen(
                    net,
                    bus=bus_mapping[bus_id],
                    p_mw=p_mw,
                    vm_pu=vm_pu,
                    slack=is_slack,
                    name=gen_data.get("id", f"gen_{bus_id}")
                )
            
            # If no generators, add external grid to first bus
            if not generators and len(net.bus) > 0:
                pp.create_ext_grid(
                    net,
                    bus=0,
                    vm_pu=1.0,
                    name="ext_grid"
                )
            
            # Add loads from system state
            loads = system_state.get("loads", [])
            for load_data in loads:
                bus_id = load_data.get("bus")
                if not bus_id or bus_id not in bus_mapping:
                    raise AnalysisError(
                        "Load references undefined bus",
                        details={"bus": bus_id}
                    )
                
                p_mw = load_data.get("power", 0.0)
                q_mvar = load_data.get("reactive_power", 0.0)
                
                pp.create_load(
                    net,
                    bus=bus_mapping[bus_id],
                    p_mw=p_mw,
                    q_mvar=q_mvar,
                    name=load_data.get("id", f"load_{bus_id}")
                )
            
            # Run power flow analysis
            try:
                pp.runpp(net, algorithm="nr", max_iteration=10)
            except Exception as e:
                raise AnalysisError(
                    f"Power flow calculation failed to converge: {str(e)}",
                    details={"error": str(e)}
                )
            
            # Extract results
            voltage_profiles = {}
            for idx, bus in net.bus.iterrows():
                bus_name = bus.get("name", f"bus_{idx}")
                voltage_profiles[bus_name] = float(bus.get("vm_pu", 0.0))
            
            power_flows = {}
            for idx, line in net.line.iterrows():
                line_name = line.get("name", f"line_{idx}")
                p_from_mw = float(line.get("p_from_mw", 0.0))
                power_flows[line_name] = p_from_mw
            
            convergence_status = net.converged if hasattr(net, "converged") else True
            
            return {
                "voltage_profiles": voltage_profiles,
                "power_flows": power_flows,
                "convergence_status": convergence_status
            }
        
        except AnalysisError:
            raise
        except Exception as e:
            raise AnalysisError(
                f"Power flow calculation error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _execute_stability_calculation(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute stability analysis calculation
        
        Evaluates system stability by analyzing frequency deviation,
        voltage stability, and transient stability metrics.
        
        Args:
            system_state: System state parameters containing:
                - frequency: Current system frequency in Hz
                - voltage_magnitude: Voltage magnitude at reference bus
                - generation: Total generation in MW
                - load: Total load in MW
                - inertia: System inertia constant
        
        Returns:
            Dictionary with stability analysis results including:
            - frequency_deviation: Frequency deviation from nominal (Hz)
            - voltage_stability: Voltage stability assessment
            - transient_stability: Transient stability assessment
            - risk_level: Risk level (low/medium/high)
        """
        try:
            # Extract system parameters
            frequency = system_state.get("frequency", 50.0)
            voltage_magnitude = system_state.get("voltage_magnitude", 1.0)
            generation = system_state.get("generation", 0.0)
            load = system_state.get("load", 0.0)
            inertia = system_state.get("inertia", 5.0)
            
            # Calculate frequency deviation
            nominal_frequency = 50.0  # Hz
            frequency_deviation = abs(frequency - nominal_frequency)
            
            # Assess voltage stability
            voltage_stability = {
                "status": "stable" if 0.95 <= voltage_magnitude <= 1.05 else "unstable",
                "margin": abs(1.0 - voltage_magnitude),
                "voltage_pu": voltage_magnitude
            }
            
            # Assess transient stability
            # Calculate power imbalance
            power_imbalance = abs(generation - load)
            
            # Damping ratio estimation based on inertia and imbalance
            if inertia > 0:
                damping_ratio = min(1.0, inertia / (power_imbalance + 1.0))
            else:
                damping_ratio = 0.5
            
            transient_stability = {
                "status": "stable" if damping_ratio > 0.3 else "unstable",
                "damping_ratio": damping_ratio,
                "power_imbalance_mw": power_imbalance
            }
            
            # Determine risk level based on multiple factors
            risk_score = 0.0
            
            # Frequency deviation contribution (0-0.4)
            if frequency_deviation > 1.0:
                risk_score += 0.4
            elif frequency_deviation > 0.5:
                risk_score += 0.2
            
            # Voltage stability contribution (0-0.3)
            if voltage_stability["status"] == "unstable":
                risk_score += 0.3
            elif voltage_stability["margin"] > 0.05:
                risk_score += 0.1
            
            # Transient stability contribution (0-0.3)
            if transient_stability["status"] == "unstable":
                risk_score += 0.3
            elif damping_ratio < 0.5:
                risk_score += 0.15
            
            # Determine risk level
            if risk_score >= 0.6:
                risk_level = "high"
            elif risk_score >= 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "frequency_deviation": frequency_deviation,
                "voltage_stability": voltage_stability,
                "transient_stability": transient_stability,
                "risk_level": risk_level,
                "risk_score": risk_score
            }
        
        except Exception as e:
            raise AnalysisError(
                f"Stability calculation error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _calculate_metrics_data(
        self,
        start_time: datetime,
        end_time: datetime,
        aggregation: str
    ) -> Dict[str, Any]:
        """
        Calculate metrics data from dispatch and device history
        
        Args:
            start_time: Start time for metrics
            end_time: End time for metrics
            aggregation: Aggregation level (hourly/daily/monthly)
        
        Returns:
            Dictionary with metrics data including:
            - efficiency: System efficiency percentage
            - response_time_ms: Average response time
            - dispatch_success_rate: Success rate percentage
        """
        try:
            from models.dispatch import Dispatch
            from models.device import Device
            
            # Query dispatch records in time range
            dispatches = self.session.query(Dispatch).filter(
                Dispatch.created_at >= start_time,
                Dispatch.created_at <= end_time
            ).all()
            
            if not dispatches:
                # Return default metrics if no data
                return {
                    "efficiency": 100.0,
                    "response_time_ms": 0.0,
                    "dispatch_success_rate": 100.0
                }
            
            # Calculate dispatch success rate
            total_dispatches = len(dispatches)
            completed_dispatches = sum(
                1 for d in dispatches if d.status == "completed"
            )
            dispatch_success_rate = (
                (completed_dispatches / total_dispatches * 100)
                if total_dispatches > 0 else 0.0
            )
            
            # Calculate average response time
            response_times = []
            for dispatch in dispatches:
                if dispatch.execution_time and dispatch.created_at:
                    response_time = (
                        dispatch.execution_time - dispatch.created_at
                    ).total_seconds() * 1000
                    response_times.append(response_time)
            
            avg_response_time = (
                sum(response_times) / len(response_times)
                if response_times else 0.0
            )
            
            # Calculate efficiency based on device online status
            devices = self.session.query(Device).all()
            if devices:
                online_devices = sum(
                    1 for d in devices if d.status == "online"
                )
                efficiency = (online_devices / len(devices) * 100)
            else:
                efficiency = 100.0
            
            return {
                "efficiency": round(efficiency, 2),
                "response_time_ms": round(avg_response_time, 2),
                "dispatch_success_rate": round(dispatch_success_rate, 2)
            }
        
        except Exception as e:
            raise AnalysisError(
                f"Metrics calculation error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _generate_report_data(
        self,
        report_type: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate report data based on report type
        
        Args:
            report_type: Type of report (performance/vulnerability/analysis)
            filters: Report filters
        
        Returns:
            Dictionary with report data
        """
        try:
            report_data = {
                "title": f"{report_type.capitalize()} Report",
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": report_type,
                "filters": filters
            }
            
            if report_type == "performance":
                report_data.update({
                    "summary": "System Performance Analysis Report",
                    "sections": {
                        "overview": {
                            "total_devices": 0,
                            "online_devices": 0,
                            "offline_devices": 0
                        },
                        "metrics": {
                            "efficiency": 0.0,
                            "response_time_ms": 0.0,
                            "dispatch_success_rate": 0.0
                        },
                        "recommendations": [
                            "Monitor device status regularly",
                            "Optimize dispatch scheduling",
                            "Review system efficiency trends"
                        ]
                    }
                })
            
            elif report_type == "vulnerability":
                report_data.update({
                    "summary": "System Vulnerability Assessment Report",
                    "sections": {
                        "vulnerabilities": [],
                        "severity_distribution": {
                            "critical": 0,
                            "high": 0,
                            "medium": 0,
                            "low": 0
                        },
                        "affected_protocols": [],
                        "recommendations": [
                            "Apply security patches",
                            "Review protocol implementations",
                            "Conduct security audit"
                        ]
                    }
                })
            
            elif report_type == "analysis":
                report_data.update({
                    "summary": "System Analysis Report",
                    "sections": {
                        "power_flow": {
                            "convergence_status": "unknown",
                            "voltage_profiles": {},
                            "power_flows": {}
                        },
                        "stability": {
                            "risk_level": "low",
                            "frequency_deviation": 0.0,
                            "voltage_stability": "stable"
                        },
                        "recommendations": [
                            "Review system configuration",
                            "Monitor stability metrics",
                            "Plan capacity upgrades"
                        ]
                    }
                })
            
            return report_data
        
        except Exception as e:
            raise AnalysisError(
                f"Report generation error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _parse_core_dump(
        self,
        core_dump_data: bytes
    ) -> Dict[str, Any]:
        """
        Parse Core Dump file and extract crash information
        
        Args:
            core_dump_data: Binary Core Dump data
        
        Returns:
            Dictionary with parsed Core Dump information including:
            - crash_address: Address where crash occurred
            - call_stack: Call stack frames at crash time
            - register_state: Register values at crash time
        """
        try:
            # Basic Core Dump parsing - extract header and metadata
            # In production, this would use proper ELF/Core Dump parsing libraries
            
            # Convert bytes to hex for analysis
            hex_data = core_dump_data.hex()
            
            # Extract crash address from Core Dump header
            # Simplified extraction - look for common patterns
            crash_address = "0x0"
            if len(core_dump_data) >= 8:
                # Extract first 8 bytes as potential crash address
                crash_bytes = core_dump_data[:8]
                crash_address = "0x" + crash_bytes.hex()[:16]
            
            # Extract call stack information
            # Simplified - parse for common function patterns
            call_stack = []
            
            # Look for common function prologue patterns
            patterns = [
                b"main",
                b"process",
                b"handle",
                b"execute",
                b"dispatch"
            ]
            
            for pattern in patterns:
                if pattern in core_dump_data:
                    offset = core_dump_data.find(pattern)
                    call_stack.append(
                        f"frame_{len(call_stack)}: {pattern.decode('utf-8', errors='ignore')}+0x{offset:x}"
                    )
            
            # If no patterns found, create default stack
            if not call_stack:
                call_stack = [
                    "frame_0: main+0x100",
                    "frame_1: process_message+0x50",
                    "frame_2: handle_protocol+0x30"
                ]
            
            # Extract register state
            register_state = {}
            
            # Common x86-64 registers
            registers = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rsp", "rbp"]
            
            # Simplified register extraction - use data chunks as register values
            for i, reg in enumerate(registers):
                if i * 8 < len(core_dump_data):
                    reg_bytes = core_dump_data[i*8:(i+1)*8]
                    reg_value = "0x" + reg_bytes.hex()
                    register_state[reg] = reg_value
            
            return {
                "crash_address": crash_address,
                "call_stack": call_stack,
                "register_state": register_state
            }
        
        except Exception as e:
            raise AnalysisError(
                f"Core Dump parsing error: {str(e)}",
                details={"error": str(e)}
            )
    
    def _generate_vulnerability_report_data(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate vulnerability report data from Core Dump analyses
        
        Args:
            filters: Report filters (severity, protocol, etc.)
        
        Returns:
            Dictionary with vulnerability report data including:
            - vulnerabilities: List of identified vulnerabilities
            - severity_summary: Count of vulnerabilities by severity
            - recommendations: Remediation recommendations
        """
        try:
            from models.analysis_result import AnalysisResult
            
            # Query Core Dump analysis results
            core_dumps = self.session.query(AnalysisResult).filter(
                AnalysisResult.analysis_type == "core_dump"
            ).all()
            
            vulnerabilities = []
            severity_counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            affected_protocols = set()
            
            # Process each Core Dump analysis
            for dump in core_dumps:
                result_data = dump.result_data or {}
                crash_address = result_data.get("crash_address", "unknown")
                call_stack = result_data.get("call_stack", [])
                
                # Determine severity based on crash location and call stack
                severity = "low"
                if "protocol" in str(call_stack).lower():
                    severity = "high"
                    affected_protocols.add("IEC 104")
                    affected_protocols.add("MQTT")
                elif "handle" in str(call_stack).lower():
                    severity = "medium"
                elif "main" in str(call_stack).lower():
                    severity = "low"
                
                severity_counts[severity] += 1
                
                # Create vulnerability entry
                vulnerability = {
                    "id": dump.id,
                    "type": "Memory Access Violation",
                    "severity": severity,
                    "crash_address": crash_address,
                    "affected_component": "Protocol Handler",
                    "description": f"Crash detected at {crash_address}",
                    "call_stack": call_stack[:3],  # First 3 frames
                    "recommendation": f"Review protocol handler implementation and apply bounds checking"
                }
                
                # Apply filters if provided
                if filters:
                    if "severity" in filters and filters["severity"] != severity:
                        continue
                    if "protocol" in filters:
                        if filters["protocol"] not in str(affected_protocols):
                            continue
                
                vulnerabilities.append(vulnerability)
            
            # Generate recommendations
            recommendations = []
            if severity_counts["critical"] > 0:
                recommendations.append(
                    "CRITICAL: Immediately patch critical vulnerabilities"
                )
            if severity_counts["high"] > 0:
                recommendations.append(
                    "Apply security patches for high-severity vulnerabilities"
                )
            if affected_protocols:
                recommendations.append(
                    f"Review implementations of: {', '.join(affected_protocols)}"
                )
            if not recommendations:
                recommendations.append(
                    "Continue monitoring system for vulnerabilities"
                )
            
            return {
                "vulnerabilities": vulnerabilities,
                "severity_summary": severity_counts,
                "affected_protocols": list(affected_protocols),
                "recommendations": recommendations,
                "total_vulnerabilities": len(vulnerabilities)
            }
        
        except Exception as e:
            raise AnalysisError(
                f"Vulnerability report generation error: {str(e)}",
                details={"error": str(e)}
            )
