import 'dart:html' as html;
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:mermaid/mermaid.dart' as mermaid;

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
    _initializeMermaid();
  }

  void _initializeMermaid() {
    if (_initialized) return;
    _initialized = true;

    // Register view factory
    ui_web.platformViewRegistry.registerViewFactory(
      _viewType,
      (int viewId) {
        // Create the main container
        final host = html.DivElement()
          ..style.width = '100%'
          ..style.height = '100%'
          ..style.overflow = 'hidden'
          ..style.backgroundColor = 'transparent'
          ..style.display = 'flex'
          ..style.justifyContent = 'center'
          ..style.alignItems = 'center';

        // Add custom styles for Mermaid diagrams
        final styleElement = html.StyleElement()
          ..text = '''
            .mermaid {
              display: flex;
              justify-content: center;
              align-items: center;
              width: 100%;
              height: 100%;
              background-color: transparent;
              padding: 20px;
            }
            .mermaid svg {
              width: auto !important;
              height: auto !important;
              max-width: 100% !important;
              max-height: 100% !important;
              object-fit: contain;
            }
            .mermaid .label {
              font-family: 'Arial', sans-serif;
              font-size: 16px !important;
              fill: white !important;
              color: white !important;
            }
            .mermaid .node rect,
            .mermaid .node circle,
            .mermaid .node ellipse,
            .mermaid .node polygon,
            .mermaid .node path {
              fill: #2A2A2A !important;
              stroke: #4A4A4A !important;
            }
            .mermaid .edgePath .path {
              stroke: #7A7A7A !important;
              stroke-width: 2px !important;
            }
            .mermaid .arrowheadPath {
              fill: #7A7A7A !important;
              stroke: none !important;
            }
            .mermaid .messageText,
            .mermaid .noteText {
              fill: white !important;
              stroke: none !important;
              font-size: 14px !important;
            }
            .mermaid .actor {
              fill: #2A2A2A !important;
              stroke: #4A4A4A !important;
            }
            .mermaid text.actor {
              fill: white !important;
              stroke: none !important;
            }
            .mermaid .note {
              fill: #2A2A2A !important;
              stroke: #4A4A4A !important;
            }
          ''';

        host.append(styleElement);

        // Add the mermaid diagram
        host.appendHtml('''
          <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center;">
            <pre class="mermaid">
${widget.diagramCode}
            </pre>
          </div>
        ''',
            validator: html.NodeValidatorBuilder()
              ..allowElement('pre', attributes: ['class'])
              ..allowElement('div', attributes: ['style'])
              ..allowElement('style')
              ..allowHtml5());

        // Initialize mermaid with custom config
        html.ScriptElement script = html.ScriptElement()
          ..text = '''
            mermaid.initialize({
              startOnLoad: true,
              theme: 'dark',
              securityLevel: 'loose',
              logLevel: 'error',
              sequence: {
                actorMargin: 80,
                messageMargin: 40,
                width: ${widget.width * 0.8},
                height: ${widget.height * 0.8},
                boxMargin: 20,
                mirrorActors: false,
                bottomMarginAdj: 20,
                useMaxWidth: true,
                wrap: false
              },
              flowchart: {
                nodeSpacing: 60,
                rankSpacing: 80,
                padding: 20,
                curve: 'basis',
                useMaxWidth: true,
                htmlLabels: true
              },
              themeVariables: {
                fontSize: '16px',
                fontFamily: 'Arial'
              }
            });
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
          ''';

        host.append(script);

        return host;
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: widget.width,
      height: widget.height,
      constraints: BoxConstraints(
        minWidth: widget.width,
        minHeight: widget.height,
      ),
      decoration: BoxDecoration(
        color: Colors.transparent,
      ),
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
