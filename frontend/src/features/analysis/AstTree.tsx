import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useNodesInitialized,
  useReactFlow,
} from '@xyflow/react'
import type { Edge, Node, NodeProps } from '@xyflow/react'
import dagre from '@dagrejs/dagre'
import { Minus, Plus, GitBranch, Maximize2 } from 'lucide-react'
import type { AstNodeResponse, SpanResponse } from '../../api/types'
import '@xyflow/react/dist/style.css'

type TreeData = { ast: AstNodeResponse; collapsed: boolean; toggle: () => void }
type TreeNode = Node<TreeData, 'ast'>
const children = (node: AstNodeResponse) => node.children ?? []
function indexTree(root: AstNodeResponse): Map<string, AstNodeResponse> {
  const index = new Map<string, AstNodeResponse>()
  function visit(node: AstNodeResponse) {
    index.set(node.id, node)
    children(node).forEach(visit)
  }
  visit(root)
  return index
}
function summary(node: AstNodeResponse): string {
  if (node.value !== null && node.value !== undefined) return String(node.value)
  if (node.value_state)
    return node.value_state === 'SIN_ASIGNAR' ? 'Sin asignar' : 'Desconocido'
  const values = new Map(children(node).map((n) => [n.label, n.value]))
  if (node.kind === 'SessionDeclaration')
    return `${values.get('Día')} · ${values.get('Hora')}`
  return String(
    values.get('Materia') ??
      values.get('Nombre') ??
      values.get('Oferta') ??
      'Lenguaje .hor',
  )
}
function nodeTone(node: AstNodeResponse) {
  return node.kind === 'Campo'
    ? 'field'
    : node.kind === 'SessionDeclaration'
      ? 'session'
      : node.kind === 'ScheduleDeclaration'
        ? 'schedule'
        : 'offer'
}
function TreeCard({ data }: NodeProps<TreeNode>) {
  const node = data.ast
  return (
    <div className={`ast-card ast-card--${nodeTone(node)}`}>
      <Handle type="target" position={Position.Left} />
      <div className="ast-card-heading">
        <GitBranch size={12} />
        <span>{node.label}</span>
        {!!children(node).length && (
          <button
            className="nodrag nopan"
            aria-label={`${data.collapsed ? 'Expandir' : 'Contraer'} ${node.label}`}
            onClick={(e) => {
              e.stopPropagation()
              data.toggle()
            }}
          >
            {data.collapsed ? <Plus size={12} /> : <Minus size={12} />}
          </button>
        )}
      </div>
      <strong title={summary(node)}>{summary(node)}</strong>
      <span className="ast-card-location">
        Línea {node.span.start.line} · Col. {node.span.start.column}
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
const nodeTypes = { ast: TreeCard }

function Canvas({
  root,
  onNavigate,
}: {
  root: AstNodeResponse
  onNavigate: (span: SpanResponse) => void
}) {
  const index = useMemo(() => indexTree(root), [root])
  const [focus, setFocus] = useState(
    children(root).length > 3 ? children(root)[0].id : root.id,
  )
  const [fields, setFields] = useState(false)
  const [collapsed, setCollapsed] = useState(
    () =>
      new Set(
        Array.from(index.values())
          .filter((n) => n.kind === 'SessionDeclaration')
          .map((n) => n.id),
      ),
  )
  const toggle = useCallback(
    (id: string) => {
      if (!fields) {
        setFields(true)
        setCollapsed((previous) => {
          const next = new Set(previous)
          next.delete(id)
          return next
        })
        return
      }
      setCollapsed((previous) => {
        const next = new Set(previous)
        if (next.has(id)) next.delete(id)
        else next.add(id)
        return next
      })
    },
    [fields],
  )
  const graph = useMemo(() => {
    const layout = new dagre.graphlib.Graph()
      .setGraph({
        rankdir: 'LR',
        nodesep: 26,
        ranksep: 64,
        marginx: 24,
        marginy: 24,
      })
      .setDefaultEdgeLabel(() => ({}))
    const nodes: TreeNode[] = []
    const edges: Edge[] = []
    function visit(ast: AstNodeResponse, parent?: string) {
      if (!fields && ast.kind === 'Campo') return
      const isCollapsed =
        collapsed.has(ast.id) ||
        (!fields && children(ast).every((n) => n.kind === 'Campo'))
      nodes.push({
        id: ast.id,
        type: 'ast',
        position: { x: 0, y: 0 },
        data: { ast, collapsed: isCollapsed, toggle: () => toggle(ast.id) },
        style: { width: 220, height: 82 },
        ariaLabel: `${ast.label}: ${summary(ast)}`,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      })
      layout.setNode(ast.id, { width: 220, height: 82 })
      if (parent) {
        layout.setEdge(parent, ast.id)
        edges.push({
          id: `${parent}-${ast.id}`,
          source: parent,
          target: ast.id,
          type: 'smoothstep',
          style: { stroke: '#8064bd', strokeWidth: 1.5 },
        })
      }
      if (!collapsed.has(ast.id))
        children(ast).forEach((child) => visit(child, ast.id))
    }
    visit(index.get(focus) ?? root)
    dagre.layout(layout)
    for (const node of nodes) {
      const position = layout.node(node.id)
      node.position = { x: position.x - 110, y: position.y - 41 }
    }
    return { nodes, edges }
  }, [root, index, focus, fields, collapsed, toggle])
  const flow = useReactFlow<TreeNode>()
  const initialized = useNodesInitialized()
  useEffect(() => {
    if (initialized)
      void flow.fitView({ padding: 0.2, maxZoom: 1, duration: 180 })
  }, [graph, initialized, flow])
  return (
    <div className="ast-panel">
      <div className="panel-tools tree-tools">
        <label className="compact-label">
          Enfoque
          <select
            aria-label="Enfoque del árbol"
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
          >
            <option value={root.id}>Programa completo</option>
            {children(root).map((node) => (
              <option key={node.id} value={node.id}>
                {node.label} · {summary(node)}
              </option>
            ))}
          </select>
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={fields}
            onChange={(e) => setFields(e.target.checked)}
          />
          Campos
        </label>
        <button
          className="text-button"
          onClick={() => {
            setFields(true)
            setCollapsed(new Set())
          }}
        >
          Expandir todo
        </button>
        <button
          className="icon-button"
          title="Ajustar árbol"
          aria-label="Ajustar árbol"
          onClick={() => {
            void flow.fitView({ padding: 0.2, maxZoom: 1, duration: 180 })
          }}
        >
          <Maximize2 size={15} />
        </button>
      </div>
      <div className="ast-viewport" aria-label="Árbol sintáctico visual">
        <ReactFlow<TreeNode>
          nodes={graph.nodes}
          edges={graph.edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
          minZoom={0.1}
          maxZoom={2.5}
          nodesDraggable={false}
          nodesConnectable={false}
          deleteKeyCode={null}
          forceColorMode="dark"
          ariaLabelConfig={{
            'controls.zoomIn.ariaLabel': 'Acercar árbol',
            'controls.zoomOut.ariaLabel': 'Alejar árbol',
            'controls.fitView.ariaLabel': 'Ajustar vista',
            'minimap.ariaLabel': 'Mapa del árbol',
          }}
          onNodeClick={(_, node) => onNavigate(node.data.ast.span)}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={22}
            size={1}
            color="#33364a"
          />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable nodeColor="#8063bd" />
        </ReactFlow>
      </div>
      <div className="tree-footer">
        <span>
          <i className="legend-dot offer" />
          Declaración <i className="legend-dot session" />
          Sesión <i className="legend-dot field" />
          Campo
        </span>
        <span>
          {graph.nodes.length}/{index.size} nodos · Selecciona uno para ubicarlo
          en el código
        </span>
      </div>
    </div>
  )
}

export default function AstTree(props: {
  root: AstNodeResponse
  onNavigate: (span: SpanResponse) => void
}) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  )
}
