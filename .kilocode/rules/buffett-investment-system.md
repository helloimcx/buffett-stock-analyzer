## Brief overview
This rule file defines development guidelines specific to the Buffett Investment System project, a value-investing focused stock monitoring and analysis platform. These rules are based on the successful implementation of multi-factor scoring, technical analysis, market environment identification, and risk management modules.

## Communication style
- Use TDD (Test-Driven Development) approach: Red-Green-Refactor cycle
- Provide detailed progress reports after each major milestone
- Focus on quantifiable improvements (e.g., signal accuracy from 65% to 75-80%)
- Maintain clear separation between analysis, design, implementation, and testing phases
- Use Chinese for user-facing communications when requested

## Development workflow
- Follow Orchestrator mode for complex multi-phase projects
- Switch to Code mode for implementation tasks
- Use Ask mode for analysis and research tasks
- Use Architect mode for system design and planning
- Always create comprehensive test suites before implementation
- Validate integration between modules after each development phase
- Generate detailed documentation for each major component

## Coding best practices
- Maintain backward compatibility with existing InvestmentScorer and StockMonitor classes
- Use dataclasses for data models with proper type hints
- Implement abstract base classes for extensible factor systems
- Follow modular design with clear separation of concerns
- Use dependency injection for testability
- Implement comprehensive error handling and data validation
- Support both synchronous and asynchronous operations where applicable

## Testing strategies
- Write failing tests first (Red phase)
- Implement minimum code to pass tests (Green phase)
- Refactor while maintaining test coverage (Refactor phase)
- Create unit tests for individual components
- Develop integration tests for module interactions
- Implement end-to-end tests for complete workflows
- Maintain >95% test coverage for critical components
- Use mock objects for external dependencies (AKShare API)

## Architectural choices
- Layered architecture: Presentation → Application → Domain → Infrastructure
- Plugin-based factor system for extensibility
- Event-driven architecture for real-time monitoring
- Microservices-ready design for future scaling
- Configuration-driven approach for factor weights and strategies
- Market-adaptive systems with dynamic parameter adjustment

## Project context
- Primary focus: Value investing with Buffett principles
- Core technologies: Python, AKShare, pandas, numpy
- Key metrics: Signal accuracy, maximum drawdown, Sharpe ratio
- Target users: Individual investors focused on value investing
- Data sources: Chinese stock market data via AKShare
- Risk tolerance: Conservative to moderate with emphasis on capital preservation

## Naming conventions
- Use descriptive names for factors: ValueFactor, GrowthFactor, QualityFactor
- Prefix test files with `test_` and place in appropriate directories
- Use snake_case for functions and variables
- Use PascalCase for classes and data types
- Include type hints for all function signatures
- Use clear, self-documenting code with minimal comments

## Performance considerations
- Optimize for batch processing of multiple stocks
- Implement caching for expensive calculations
- Use vectorized operations with numpy/pandas
- Monitor memory usage for large datasets
- Target response times <200ms for real-time operations
- Support concurrent processing where beneficial

## Documentation requirements
- Create comprehensive README files for each module
- Include usage examples in docstrings
- Generate API documentation for public interfaces
- Maintain changelog for version tracking
- Provide integration guides for new features
- Create visual diagrams for complex architectures

## Quality assurance
- Conduct code reviews for all major components
- Perform load testing for high-traffic scenarios
- Validate data accuracy against multiple sources
- Test edge cases and error conditions
- Ensure graceful degradation for external service failures
- Monitor system performance in production environments