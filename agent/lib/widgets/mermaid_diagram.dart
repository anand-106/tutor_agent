import 'dart:html' as html;
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';

class MermaidDiagram extends StatefulWidget {
  final String diagramCode;
  final double width;
  final double height;

  const MermaidDiagram({
    Key? key,
    required this.diagramCode,
    this.width = 600,
    this.height = 400,
  }) : super(key: key);

  @override
  State<MermaidDiagram> createState() => _MermaidDiagramState();
}

class _MermaidDiagramState extends State<MermaidDiagram> {
  late final String _viewType;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _viewType = 'mermaid-${DateTime.now().millisecondsSinceEpoch}';
    print('MermaidDiagram initialized with viewType: $_viewType');
    _initializeMermaid();
  }

  void _initializeMermaid() {
    if (_initialized) return;
    _initialized = true;

    print('Starting Mermaid initialization...');

    // Register view factory
    ui_web.platformViewRegistry.registerViewFactory(_viewType, (int viewId) {
      print('Creating view for Mermaid diagram...');
      print('ViewId: $viewId');

      // Clean up the code by removing problematic characters and fixing syntax
      String formattedCode = widget.diagramCode.trim();

      // Ensure proper diagram type prefix
      if (!formattedCode.startsWith('classDiagram') &&
          !formattedCode.startsWith('graph') &&
          !formattedCode.startsWith('sequenceDiagram')) {
        if (formattedCode.contains('class ')) {
          formattedCode = 'classDiagram\n' + formattedCode;
        } else {
          formattedCode = 'graph TD\n' + formattedCode;
        }
      }

      print('Formatted diagram code: $formattedCode');

      // Create wrapper container for zoom controls and diagram
      final wrapperContainer = html.DivElement()
        ..style.width = '${widget.width}px'
        ..style.height = '${widget.height}px'
        ..style.position = 'relative'
        ..style.backgroundColor = 'transparent';

      // Create zoom controls
      final zoomControls = html.DivElement()
        ..style.position = 'absolute'
        ..style.top = '10px'
        ..style.right = '10px'
        ..style.zIndex = '100'
        ..style.display = 'flex'
        ..style.gap = '5px'
        ..style.backgroundColor = 'rgba(0, 0, 0, 0.5)'
        ..style.padding = '5px'
        ..style.borderRadius = '4px';

      // Create zoom in button
      final zoomInBtn = html.ButtonElement()
        ..innerText = '+'
        ..style.width = '30px'
        ..style.height = '30px'
        ..style.border = '1px solid #ffffff40'
        ..style.borderRadius = '4px'
        ..style.backgroundColor = '#2A2A2A'
        ..style.color = 'white'
        ..style.cursor = 'pointer'
        ..style.fontSize = '18px'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center';

      // Create zoom out button
      final zoomOutBtn = html.ButtonElement()
        ..innerText = '−'
        ..style.width = '30px'
        ..style.height = '30px'
        ..style.border = '1px solid #ffffff40'
        ..style.borderRadius = '4px'
        ..style.backgroundColor = '#2A2A2A'
        ..style.color = 'white'
        ..style.cursor = 'pointer'
        ..style.fontSize = '18px'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center';

      // Create reset zoom button
      final resetZoomBtn = html.ButtonElement()
        ..innerText = '⟲'
        ..style.width = '30px'
        ..style.height = '30px'
        ..style.border = '1px solid #ffffff40'
        ..style.borderRadius = '4px'
        ..style.backgroundColor = '#2A2A2A'
        ..style.color = 'white'
        ..style.cursor = 'pointer'
        ..style.fontSize = '18px'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center';

      zoomControls.children.addAll([zoomInBtn, zoomOutBtn, resetZoomBtn]);

      // Create container with unique ID
      final container = html.DivElement()
        ..id = _viewType
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.backgroundColor = 'transparent'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..style.overflow = 'hidden'
        ..style.position = 'relative';

      // Create diagram element
      final diagramElement = html.DivElement()
        ..className = 'mermaid'
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..text = formattedCode;

      container.children.add(diagramElement);
      wrapperContainer.children.addAll([container, zoomControls]);

      // Add script to render diagram with zoom and pan functionality
      final script = html.ScriptElement()
        ..text = '''
          (function() {
            let currentScale = 1;
            let isDragging = false;
            let startX, startY, translateX = 0, translateY = 0;
            const MIN_SCALE = 0.1;
            const MAX_SCALE = 5;
            const SCALE_STEP = 0.05;  // Reduced from 0.1 for smoother zooming
            const WHEEL_SCALE_FACTOR = 0.0005;  // Fine-tuned wheel zoom sensitivity

            function updateTransform() {
              const svg = document.querySelector('#${_viewType} svg');
              if (svg) {
                // Apply transform origin to the center of the viewport
                svg.style.transformOrigin = '50% 50%';
                svg.style.transform = `translate(\${translateX}px, \${translateY}px) scale(\${currentScale})`;
              }
            }

            function handleZoom(delta, clientX, clientY) {
              const svg = document.querySelector('#${_viewType} svg');
              if (!svg) return;

              const container = document.querySelector('#${_viewType}');
              const containerRect = container.getBoundingClientRect();
              const svgRect = svg.getBoundingClientRect();

              // Calculate relative position within the container
              const relativeX = (clientX - containerRect.left) / containerRect.width;
              const relativeY = (clientY - containerRect.top) / containerRect.height;

              // Store old dimensions
              const oldWidth = svgRect.width * currentScale;
              const oldHeight = svgRect.height * currentScale;

              // Update scale with the new delta
              const oldScale = currentScale;
              currentScale = Math.min(Math.max(currentScale * (1 + delta), MIN_SCALE), MAX_SCALE);

              // Calculate new dimensions
              const newWidth = svgRect.width * currentScale;
              const newHeight = svgRect.height * currentScale;

              // Adjust translation to maintain the zoom point position
              translateX += (oldWidth - newWidth) * relativeX;
              translateY += (oldHeight - newHeight) * relativeY;

              updateTransform();
            }

            // Add zoom event listeners
            document.querySelector('button:nth-child(1)').addEventListener('click', () => {
              const svg = document.querySelector('#${_viewType} svg');
              if (svg) {
                const rect = svg.getBoundingClientRect();
                handleZoom(SCALE_STEP * 2, rect.left + rect.width / 2, rect.top + rect.height / 2);
              }
            });

            document.querySelector('button:nth-child(2)').addEventListener('click', () => {
              const svg = document.querySelector('#${_viewType} svg');
              if (svg) {
                const rect = svg.getBoundingClientRect();
                handleZoom(-SCALE_STEP * 2, rect.left + rect.width / 2, rect.top + rect.height / 2);
              }
            });

            document.querySelector('button:nth-child(3)').addEventListener('click', () => {
              currentScale = 1;
              translateX = 0;
              translateY = 0;
              updateTransform();
            });

            // Add pan event listeners with improved sensitivity
            const container = document.querySelector('#${_viewType}');
            let lastX, lastY;
            
            container.addEventListener('mousedown', (e) => {
              if (e.button === 0) { // Left click only
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
                container.style.cursor = 'grabbing';
              }
            });

            window.addEventListener('mousemove', (e) => {
              if (isDragging) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                translateX += dx;
                translateY += dy;
                
                lastX = e.clientX;
                lastY = e.clientY;
                
                updateTransform();
              }
            });

            window.addEventListener('mouseup', () => {
              isDragging = false;
              container.style.cursor = 'grab';
            });

            // Add wheel zoom support with improved sensitivity
            container.addEventListener('wheel', (e) => {
              e.preventDefault();
              const wheelDelta = e.deltaY * WHEEL_SCALE_FACTOR;
              handleZoom(-wheelDelta, e.clientX, e.clientY);
            }, { passive: false });

            // Initialize cursor style
            container.style.cursor = 'grab';

            function renderDiagram() {
              if (typeof mermaid === 'undefined') {
                console.log('Waiting for Mermaid to load...');
                setTimeout(renderDiagram, 100);
                return;
              }

              try {
                console.log('Rendering diagram for ${_viewType}');
                mermaid.run({
                  querySelector: '#${_viewType} .mermaid',
                  suppressErrors: false
                }).then(() => {
                  console.log('Render successful for ${_viewType}');
                  const svg = document.querySelector('#${_viewType} svg');
                  if (svg) {
                    svg.style.maxWidth = '100%';
                    svg.style.maxHeight = '100%';
                    svg.style.width = 'auto';
                    svg.style.height = 'auto';
                    svg.style.backgroundColor = 'transparent';
                    svg.style.transition = 'none'; // Remove transition for smoother pan/zoom
                    
                    // Calculate and set viewBox
                    const bbox = svg.getBBox();
                    const padding = 20;
                    svg.setAttribute('viewBox', 
                      `\${bbox.x - padding} \${bbox.y - padding} \${bbox.width + padding * 2} \${bbox.height + padding * 2}`
                    );
                    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

                    // Set high-quality rendering
                    svg.style.shapeRendering = 'geometricPrecision';
                    svg.style.textRendering = 'optimizeLegibility';
                    svg.style.imageRendering = 'optimizeQuality';
                    
                    // Enable pointer events on SVG elements
                    svg.style.pointerEvents = 'all';
                  }
                }).catch(error => {
                  console.error('Render error:', error);
                  const errorDiv = document.createElement('div');
                  errorDiv.style.color = '#ff6b6b';
                  errorDiv.style.padding = '16px';
                  errorDiv.innerHTML = `Error rendering diagram: \${error.message || 'Unknown error'}`;
                  document.querySelector('#${_viewType}').appendChild(errorDiv);
                });
              } catch (error) {
                console.error('Error in render:', error);
              }
            }
            renderDiagram();
          })();
        ''';

      wrapperContainer.children.add(script);
      return wrapperContainer;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: widget.width,
      height: widget.height,
      decoration: BoxDecoration(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      clipBehavior: Clip.hardEdge,
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
