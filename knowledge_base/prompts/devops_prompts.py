"""
DevOps prompt templates for F-Ops AI Agent
These templates guide the LLM in generating appropriate DevOps solutions
"""

PROMPT_TEMPLATES = {
    "zero_to_deploy": """
    Analyze the repository at {repo_url} and create a complete deployment pipeline.
    
    Stack detected: {stack}
    Target environment: {environment}
    Deployment target: {target}
    
    Generate:
    1. CI/CD pipeline configuration
    2. Infrastructure as Code templates
    3. Deployment scripts
    4. Environment-specific configurations
    5. Security policies
    
    Requirements:
    - Use best practices for {stack}
    - Include security scanning
    - Implement proper secret management
    - Add health checks and monitoring
    - Ensure zero-downtime deployments
    - Include rollback mechanisms
    
    Output format:
    - Provide complete, production-ready configurations
    - Include inline comments explaining key decisions
    - List any assumptions made
    - Suggest next steps for optimization
    """,
    
    "incident_analysis": """
    Analyze the incident for service: {service_name}
    
    Current symptoms:
    {symptoms}
    
    Recent changes:
    {recent_changes}
    
    Metrics data:
    {metrics}
    
    Log excerpts:
    {log_samples}
    
    Provide:
    1. Root cause analysis with evidence
    2. Immediate mitigation steps (prioritized by impact)
    3. Long-term fix recommendations
    4. Prevention strategies
    5. Similar incidents from knowledge base
    
    Consider:
    - Service dependencies and cascading failures
    - Recent deployments or configuration changes
    - External factors (upstream services, infrastructure)
    - Historical patterns from past incidents
    
    Format response with clear sections and actionable steps.
    """,
    
    "infrastructure_optimization": """
    Review the current infrastructure and suggest optimizations.
    
    Current setup:
    {infrastructure_details}
    
    Usage patterns:
    {usage_metrics}
    
    Cost data:
    {cost_breakdown}
    
    Performance metrics:
    {performance_data}
    
    Recommend:
    1. Cost optimization strategies with estimated savings
    2. Performance improvements with expected gains
    3. Scaling recommendations based on usage patterns
    4. Security enhancements and compliance gaps
    5. Disaster recovery improvements
    
    Prioritize recommendations by:
    - ROI (cost savings vs. implementation effort)
    - Risk reduction
    - Performance impact
    - Implementation complexity
    
    Include specific actions and estimated timelines.
    """,
    
    "pipeline_generation": """
    Generate a CI/CD pipeline for the following project:
    
    Repository: {repository}
    Technology stack: {tech_stack}
    Build system: {build_system}
    Test framework: {test_framework}
    Target platform: {platform}
    Environments: {environments}
    
    Requirements:
    - Multi-stage pipeline (build, test, security, deploy)
    - Parallel execution where possible
    - Caching for dependencies and build artifacts
    - Security scanning (SAST, dependency check)
    - Test coverage reporting
    - Artifact management
    - Environment-specific deployments
    - Approval gates for production
    
    Generate complete pipeline configuration for {ci_system}.
    Include best practices and optimization techniques.
    """,
    
    "kubernetes_manifest": """
    Generate Kubernetes manifests for deploying:
    
    Application: {app_name}
    Type: {app_type}
    Image: {container_image}
    Replicas: {replicas}
    Resources: {resource_requirements}
    Exposed ports: {ports}
    Environment variables: {env_vars}
    Persistent storage: {storage_requirements}
    
    Generate:
    1. Deployment manifest with proper resource limits
    2. Service manifest for internal/external access
    3. ConfigMap for configuration
    4. Secret manifest template
    5. HorizontalPodAutoscaler for auto-scaling
    6. NetworkPolicy for security
    7. PodDisruptionBudget for availability
    
    Include:
    - Health checks (liveness and readiness probes)
    - Security context and pod security policies
    - Anti-affinity rules for high availability
    - Proper labels and annotations
    """,
    
    "terraform_infrastructure": """
    Generate Terraform configuration for:
    
    Cloud provider: {cloud_provider}
    Environment: {environment}
    Application type: {app_type}
    Components needed: {components}
    Network requirements: {network_config}
    Security requirements: {security_requirements}
    
    Generate:
    1. Provider configuration
    2. Network infrastructure (VPC, subnets, security groups)
    3. Compute resources
    4. Database infrastructure
    5. Storage configuration
    6. Load balancing
    7. Monitoring and alerting
    8. IAM roles and policies
    
    Follow best practices:
    - Use modules for reusability
    - Implement proper state management
    - Include variable definitions
    - Add output values
    - Use data sources where appropriate
    - Include tags for resource management
    """,
    
    "security_audit": """
    Perform a security audit for:
    
    Service: {service_name}
    Technology: {technology}
    Current security measures: {current_security}
    Compliance requirements: {compliance_needs}
    
    Analyze:
    1. Authentication and authorization mechanisms
    2. Data encryption (at rest and in transit)
    3. Secret management practices
    4. Network security configuration
    5. Vulnerability assessment
    6. Compliance gaps
    7. Access control and audit logging
    8. Incident response readiness
    
    Provide:
    - Critical vulnerabilities requiring immediate action
    - High-priority security improvements
    - Compliance remediation steps
    - Security best practices recommendations
    - Implementation roadmap with priorities
    """,
    
    "performance_tuning": """
    Analyze and optimize performance for:
    
    Service: {service_name}
    Current metrics:
    - Response time: {response_time}
    - Throughput: {throughput}
    - Error rate: {error_rate}
    - Resource usage: {resource_usage}
    
    Bottlenecks identified: {bottlenecks}
    
    Provide optimization recommendations for:
    1. Application-level optimizations
    2. Database query optimization
    3. Caching strategies
    4. Resource allocation tuning
    5. Network optimization
    6. Load balancing improvements
    7. Auto-scaling configuration
    
    Include:
    - Expected performance gains
    - Implementation complexity
    - Risk assessment
    - Monitoring requirements
    """,
    
    "disaster_recovery": """
    Design a disaster recovery plan for:
    
    Application: {application}
    Critical services: {critical_services}
    RTO requirement: {rto}
    RPO requirement: {rpo}
    Current backup strategy: {backup_strategy}
    
    Provide:
    1. Backup and restoration procedures
    2. Failover mechanisms
    3. Data replication strategy
    4. Communication plan
    5. Testing procedures
    6. Documentation requirements
    
    Consider:
    - Multi-region deployment strategies
    - Database replication and consistency
    - DNS failover configuration
    - Monitoring and alerting for DR events
    - Regular DR testing schedule
    """,
    
    "monitoring_setup": """
    Design a comprehensive monitoring strategy for:
    
    Services: {services}
    Infrastructure: {infrastructure}
    SLO requirements: {slo_requirements}
    
    Configure:
    1. Metrics collection (application, infrastructure, custom)
    2. Log aggregation and analysis
    3. Distributed tracing
    4. Alerting rules and thresholds
    5. Dashboard creation
    6. SLI/SLO tracking
    7. Incident detection and escalation
    
    Include:
    - Specific metrics to track
    - Alert conditions and severity levels
    - Dashboard layouts and visualizations
    - Integration with incident management
    - Retention policies
    """,
    
    "code_review": """
    Review the code changes for:
    
    Pull request: {pr_details}
    Changed files: {changed_files}
    Diff summary: {diff_summary}
    
    Analyze:
    1. Code quality and maintainability
    2. Security vulnerabilities
    3. Performance implications
    4. Test coverage
    5. Documentation completeness
    6. Architectural consistency
    7. Best practices adherence
    
    Provide:
    - Critical issues that must be addressed
    - Suggestions for improvement
    - Security concerns
    - Performance optimization opportunities
    - Positive feedback on good practices
    """,
    
    "capacity_planning": """
    Perform capacity planning analysis for:
    
    Service: {service_name}
    Current usage: {current_metrics}
    Growth projections: {growth_data}
    Peak patterns: {peak_patterns}
    
    Calculate and recommend:
    1. Resource requirements for projected growth
    2. Scaling thresholds and policies
    3. Cost projections
    4. Database capacity needs
    5. Network bandwidth requirements
    6. Storage growth predictions
    
    Consider:
    - Seasonal variations
    - Marketing campaigns or events
    - Feature launches
    - Geographic expansion
    - Buffer for unexpected growth
    """
}