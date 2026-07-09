# Extracted from update2.docx

GraphPrompt-MAS 研究方向修改版

基于 Prompt Node 的 LLM MAS with Graph Organization

## 1. 研究背景

LLM 多智能体系统的效果不仅取决于单个 agent 的能力，也取决于这些 agent 如何被组织成图、如何共享状态以及如何控制信息流。对于同一个任务，链式通信、全连接通信、基于 group 的通信以及动态生成的图组织方式，会带来不同的错误传播、洞察传播和 token 成本。因此，本文不再把问题表述为单纯的 MAS 通信拓扑改善，而是提升为 MAS with graph organization：agent 角色、通信边、共享状态、局部 group 和运行时路由共同决定系统表现。

已有工作分别从剪枝、graph organization 生成、group 组织、异构模型调度和运行时修复等角度说明：真实智能体节点和真实通信边可以被优化。但这些方法大多仍然围绕“真实节点 / 真实边”做增删改，缺少一种介于普通 prompt 和完整智能体之间的中间粒度组织单元。本文希望通过 Prompt Node，让 MAS 不只是“连边更多或更少”，而是形成更可解释、更可更新、更可控成本的图组织结构。

图提示学习提供了一个有启发性的视角：prompt 不一定只以自然语言前缀的形式存在，也可以作为图中的结构化提示单元参与下游任务。把这个思想迁移到 MAS 场景中，就可以进一步思考：是否能在真实智能体和真实通信边之外，引入更轻量、更可控的虚拟功能节点，将原始 MAS 从普通通信图升级为 MAS with graph organization。

## 2. 当下研究问题的局限

从现有论文可以看到一个比较集中的问题：很多方法要么只删除低贡献信息来降低成本，要么直接生成新的 agent 或 group 来增强能力。前者容易丢失关键洞察或共享记忆，后者代价较高，也可能让系统结构变得更复杂。边级学习虽然能调节传播强度，但不容易显式表达“这里需要一个具体功能节点”。

因此，本文希望回答的问题不是简单地“要不要多连一条边”或“要不要再加一个完整智能体”，而是：在当前 MAS graph organization 中，是否存在某种缺失的轻量组织功能，例如共享记忆、局部指令、冲突检查、工具说明，或者需要被升级成 agent-like 的临时职责。

## 3. 我们的方法：Prompt Node Augmented MAS with Graph Organization

针对上述局限，本文的方法是在不频繁新增完整智能体、不完全重建 MAS 的情况下，向原始 MAS graph organization 中插入可解释、可读写、可更新、可裁剪的虚拟功能节点。原始图中的真实智能体仍负责推理、检索、批判、总结和工具调用；Prompt Node 则负责保存共享状态、维护局部规则、检查冲突、提示工具资源，并通过连接位置和读写路由改善整体组织方式。

本文提出的 Prompt Node 不是普通自然语言提示词，也不必是独立调用模型的真实智能体。它是放在 MAS 图组织中的轻量功能节点，具有身份类型、结构化内容、连接位置、读写权限和生命周期。这样一来，本文讨论的就不只是“多加几个 prompt”，而是把 prompt 明确纳入 MAS with graph organization，使其成为可被诊断、插入、更新和裁剪的组织单元。

为了避免概念混乱，本文把 Prompt Node 拆成三层描述。第一层是身份类型，回答“这个节点是什么”；第二层是插入模式，回答“这个节点放在哪里、连接谁”；第三层是生命周期行为，回答“插入后如何更新、路由、剪枝、合并或升级”。Bridge、Group、Router 不再作为并列身份类型，而是属于 MAS graph organization 中的连接模式、共享范围或运行时行为。这样既能保持 Prompt Node 类型足够简洁，也能把研究表述从通信拓扑改善提升到图组织增强。

图 1 Prompt-Node Augmented MAS with Graph Organization 的整体流程：先诊断图组织状态，再选择身份并初始化插入 Prompt Node，随后在多轮通信中更新、路由和管理生命周期。

增强后的 MAS with graph organization 可以直观理解为两层结构。第一层是真实智能体和真实通信边，负责完成任务中的推理、检索、批判、总结等操作。第二层是 Prompt Node 及其连接边，负责保存关键中间结论、检查冲突、维护局部规则或工具说明，并通过读写路由决定哪些信息应被共享、压缩、阻断或升级为 agent-like 行为。

图 2 Prompt Node 在 MAS Graph Organization 中的身份类型、插入模式与生命周期行为：身份类型控制在三到四类，Bridge、Group、Router 作为连接位置或运行时行为。

## 4. 技术点一：Prompt Node 定义、身份选择与 Graph Organization 初始化

第一个技术点回答“我们到底要插入什么，以及插在哪里”。如果 Prompt Node 的身份没有定义清楚，后续动态更新和实验实现都会变成随意加 prompt。因此，技术点一主要处理初始化过程：先把当前 MAS 运行过程表示成可诊断的 graph organization 属性图，再诊断其中缺失的组织功能，最后选择 Prompt Node 身份并完成插入。

这个技术点内部应保持顺序关系：先建模图状态，再诊断缺陷并选择身份，最后把选出的 Prompt Node 接入原始 MAS。运行时剪枝、删除、合并或升级属于技术点二，不应混在初始化阶段里。

### 4.1 计算模块一：MAS Graph Organization 属性建模

这个模块的作用是把当前 MAS 的角色分工、通信边、工具配置、轮次历史和局部 group 关系转成一张带属性的图，为后面的诊断和插入提供可计算状态。图中既保留真实智能体节点，也保留通信边、轮次信息、token 成本、消息新颖性、引用关系、工具使用和层级结构等信号。这里的重点不是只建模“谁和谁通信”，而是建模 MAS 的整体 graph organization。

这一模块吸收了 AgentPrune 对 spatial / temporal communication 的划分，也吸收了 EIB-Learner 的 attributed graph 表示。但本文与它们的区别在于：图表示不只服务于边学习或边剪枝，还要为后续插入虚拟 Prompt Node 预留组织位置，使 Prompt Node 成为 MAS graph organization 的可操作组件。

### 4.2 计算模块二：Graph Organization 缺陷诊断与身份选择

有了图状态后，系统先诊断当前 graph organization 的缺陷，而不是直接插入节点。这样做的原因是：只有先知道 MAS 在组织上哪里出了问题，Prompt Node 的身份选择才不是随机的。这个模块需要回答：当前更需要 Memory、Instruction / Verifier、Tool / Resource，还是需要升级为 Agent-like。

身份选择可以先写成一个直观优先级，而不是第一版就训练复杂模型：Prompt Node 优先级 = 缺陷强度 + 身份匹配度 + 位置相关性 + 预计 EIB 收益 - 额外成本 - 冗余风险。也就是说，一个 Prompt Node 是否值得插入，取决于它能否解决当前缺陷、是否放在合适位置、能否抑制错误或传播洞察，以及它带来的 token 开销是否可接受。

### 4.3 计算模块三：Prompt Node 内容初始化与插入模式生成

选出身份后，系统需要初始化节点内容，并决定它连接到哪些 agent 或子图。这里可以借鉴 ProG 的三部分视角：节点内容对应 prompt token，多个 Prompt Node 的组织对应 token structure，连接到真实智能体 的方式对应 insert pattern。

连接位置不能默认全局广播，而应由结构和语义共同决定。Memory 应靠近产生关键洞察的 source agent 和后续需要该信息的 consumer agent；Instruction / Verifier 应连接冲突双方、critic 和 aggregator；Tool / Resource 应连接需要共享工具说明或资料摘要的 agent；Agent-like 则应放在能力缺口最明显的位置。换言之，插入模式本身就是 MAS graph organization 的一部分。

## 5. 技术点二：Prompt Node 驱动的 Graph Organization 动态迭代与生命周期管理

第二个技术点回答 Prompt Node 插入之后如何继续发挥作用。若 Prompt Node 只是一次性文本，它和普通 prompt 区别不大；本文需要强调它有生命周期：可以被读取、写入、压缩和更新，可以控制路由，也可以在贡献不足时被剪枝、删除或合并，在轻量提示不足时升级为 Agent-like 节点。

这个技术点对应“插错了怎么办、要不要删掉、如何继续发挥作用”的问题。它不是重新定义 Prompt Node 身份，而是在技术点一的初始插入基础上进行动态迭代。

图 3 MAS Graph Organization 的动态迭代闭环：Prompt Node 插入之后经过读写路由、状态更新、贡献评估和生命周期动作，形成可控的运行时更新过程。

### 5.1 计算模块一：Prompt Node 状态更新

每个 Prompt Node 都维护一个小型状态，记录它的身份类型、当前内容、连接对象、未解决问题、最近被引用情况、置信度、token 成本和实际贡献。每一轮通信结束后，节点状态根据新消息更新：有价值的信息被保留，重复或过期内容被删除，新的冲突和待验证点被加入。

为了让这个过程直观，可以把状态更新理解为一句话：新状态 = 旧状态 + 本轮消息 + agent 输出 + 当前图状态。这样既保留了递推关系，又避免在第一版中把方法写得过度数学化。

### 5.2 计算模块二：Agent-Prompt 一致性建模与读写路由

路由模块需要判断哪个 agent 真的需要读取或写入某个 Prompt Node。这个模块可以看作 EIB-Learner 中“agent 之间一致性建模”的延伸，只不过这里建模的不是 agent 与 agent 的一致性，而是 agent 与 Prompt Node 的功能匹配程度。

一致性分数不一定要先写成复杂模型，第一版可以从五个角度判断：agent 当前子任务是否与节点内容相关；agent 是否参与了该节点记录的冲突；agent 是否可靠到可以写入共享节点；该读写路径是否值得额外 token 成本；以及节点是否服务于某个局部 group 或层级结构。

基于这些判断，系统生成三类路由。Read routing 决定哪个 agent 读取某个 Prompt Node；Write routing 决定哪个 agent 的输出可以写入某个 Prompt Node；Forward routing 决定 Prompt Node 是否把压缩后的信息转发给其他 agent。这样可以避免所有 agent 阅读所有历史。

### 5.3 计算模块三：EIB-aware 自适应路由与生命周期动作

这里直接使用 EIB-Learner 的主要直觉：稀疏通信有利于限制错误扩散，较密的局部通信有利于传播有价值洞察。因此，Prompt Node 的路由不固定选择稀疏或稠密，而是根据当前 graph organization 状态切换。

具体来说，可以保留两个路由视角：错误抑制视角倾向于阻断低可信消息、减少广播并限制错误写入；洞察传播视角倾向于让高质量结论跨 agent 或跨 group 传播。最终路由由这两个视角加权得到：冲突强、置信度低时更偏向错误抑制；多个高质量 agent 产生一致洞察时，更偏向洞察传播。

生命周期管理用于防止 Prompt Node 本身变成新的冗余。贡献可以从四个角度评估：后续 agent 是否引用该节点，最终答案或一致性是否提升，token 是否下降，以及错误扩散是否被阻止。低贡献节点被剪枝，重复节点被合并；如果某个节点反复需要复杂推理或工具调用，则升级为 Agent-like Prompt Node。

## 6. 最小可实现版本与实验验证

为了尽快进入代码开发，第一版不必实现所有身份和所有生命周期动作。建议先做三类身份：Memory Prompt Node、Instruction / Verifier Prompt Node、Agent-like Prompt Node。Tool / Resource 可以作为第二版扩展。Bridge 不作为身份实现，而作为插入模式贯穿 Memory 和 Instruction / Verifier 两类节点。

第一版流程可以写成如下五步：

先运行一轮普通 MAS，收集 agent 输出、互评结果、token 成本、引用关系和冲突信号。

构建 MAS graph organization 属性图，诊断共享记忆缺失、答案冲突、关键洞察未传播和子图信息孤岛。

根据诊断选择 Prompt Node 身份，生成初始内容、连接位置和读写权限；桥接只作为连接模式。

第二轮让相关 agent 读取或写入 Prompt Node，并根据状态更新进行路由、压缩、剪枝或升级。

比较原始 MAS 与增强 MAS 在准确率、token 成本、冲突解决率和关键洞察引用率上的差异。

## 7. 总结

这份方案的重点不是增加更多 agent，而是提出一种更细粒度的 MAS graph organization 增强方式。Prompt Node 作为介于普通 prompt 和完整智能体之间的结构单元，可以在成本更低的情况下补齐 MAS 图组织中的功能缺口。

从方法结构上看，本文可以围绕两个技术点展开：第一，Prompt Node 如何被定义、选择身份并初始化插入；第二，Prompt Node 插入后如何更新、路由、剪枝、合并或升级。前者对应“插什么、插在哪里”，后者对应“插入后如何持续有效”。整体叙事由“通信拓扑改善”升级为“MAS with Graph Organization”。

## Table 1
| 版本定位 这份文档面向组会讨论，按“研究背景、当下局限、本文方法、两个技术点”的顺序展开。根据最新建议，本文把研究表述从“MAS 通信拓扑改善”升级为 MAS with Graph Organization，即同时考虑 agent 角色、通信边、共享状态、局部 group 和运行时路由。Prompt Node 仍统一定义为插入 MAS 图组织中的虚拟功能节点；Bridge / Group / Router 不作为并列身份，而作为插入模式或生命周期行为。 |

## Table 2
| 已有方向 | 论文中的主要做法 | 对本文的启发 |
| AgentPrune / AgentDropout | 把 MAS 看成可剪枝的图结构，删除低贡献信息，降低 token 成本。 | 只做删减不够，还需要主动补充缺失的组织功能。 |
| EIB-Learner | 分析稀疏图和稠密图对错误传播、洞察传播的不同影响，提出 error-insight balance。 | Prompt Node 的路由不应固定追求稀疏或稠密，而应根据任务状态决定哪些信息扩散、哪些信息收缩。 |
| ARG / ADG-DESIGNER | 从任务出发自回归生成 agent role 和通信边，摆脱固定模板式图组织。 | 动态扩展是有价值的；当所有 Prompt Node 都选择 Agent-like 身份时，这类方法可视为本文的一种特殊情况。 |
| GoAgent / Group 方法 | 把协作 group 作为 graph organization 的基本单位，减少 node-centric 设计带来的割裂。 | Group 可以作为 Prompt Node 的插入模式或共享上下文范围，而不是必须作为独立身份类型。 |
| GoA | 从模型池中选择相关 LLM，再做相关性驱动的 message passing 和 pooling。 | Prompt Node 的连接位置也应考虑任务相关性、消息可信度、预计收益和额外成本。 |
| MAS2 | 用 Generator、Implementor、Rectifier 支持运行时修复完整 MAS 工作流。 | 运行时修复很重要，但本文选择更细粒度的 graph organization 修复，而不是重建整个工作流。 |
| ProG | 把图提示拆成 prompt tokens、token structure、insert patterns，并从效果、灵活性、效率评价 prompt。 | Prompt Node 可以对应到身份内容、内部组织和插入位置三部分，评价也应同时看效果、成本和传播质量。 |

## Table 3
| Prompt Node 身份类型 | 主要作用 | 设计动机与连接方式 |
| Memory Prompt Node | 保存关键事实、中间结论、共享约束和被多次引用的推理。 | 补充剪枝方法只会删减的问题，避免重要信息因图太稀或历史太长而丢失；通常连接 source agent、consumer agent 和 aggregator。 |
| Instruction / Verifier Prompt Node | 保存局部指令、检查标准、冲突清单、证据强弱和待验证问题。 | 对应错误抑制需求，使低可信答案不轻易扩散；通常连接冲突双方、critic 和最终聚合节点。 |
| Tool / Resource Prompt Node | 保存工具使用规范、API 参数、检索资料摘要或外部资源说明。 | 用于把工具和资料组织成可被多个 agent 共享的轻量节点；第一版可作为扩展功能，不必优先实现。 |
| Agent-like Prompt Node | 当轻量提示不足时，升级为可独立推理、调用工具或承担新角色的节点。 | 把 ARG / ADG-DESIGNER 的新增 agent 视为一种更高成本的后备操作；当所有 Prompt Node 都是 Agent-like 时，本文方法退化为 agent 生成类方法。 |

## Table 4
| 组织作用或运行时行为 | 在本文中的定位 | 例子 |
| Bridge | 插入模式，不是身份类型。任何身份的 Prompt Node 都可以通过连接两个弱通信子图起到桥接作用。 | 一个 Memory 节点放在数学组和代码组之间，把约束条件转成代码组可用的共享状态。 |
| Group | 共享上下文范围，不是必需的身份类型。Prompt Node 可以服务于某个临时 group。 | 一个 Instruction / Verifier 节点只被局部小组读写，用于维护共同目标和检查标准。 |
| Router | 生命周期中的路由行为，不是单独身份。系统根据一致性、可靠性和预算决定读写与转发。 | 低可信长消息不再全局广播，只把压缩摘要写入 Memory 或交给 Verifier 检查。 |

## Table 5
| 对象 | 实现中记录的表示 | 包含的信息 |
| Agent 节点 | agent 表示 = 任务 + 角色 + 模型 / 工具配置 + 当前输出 + 历史状态 | 任务 q、agent 角色、工具或模型、当前输出、历史正确性、置信度和可写入权限。 |
| 通信边 | 边表示 = 源节点 + 目标节点 + 消息内容 + 轮次 + token 成本 + 新信息量 | 消息语义、发生轮次、成本、novelty、可靠性，以及是否被后续 agent 或 aggregator 引用。 |
| 候选插入位置 | 候选位置 = source-consumer 对 + 冲突中心 + group 边界 + aggregator 前检查点 | 可能需要共享记忆、局部检查、工具说明或 agent-like 升级的位置。 |
| 组织级状态 | 图状态 = 节点表示 + 边表示 + 冲突信号 + 预算统计 + 引用关系 | 整张图当前的协作状态，包括不确定性、预算消耗、错误传播风险和关键洞察传播情况。 |

## Table 6
| 诊断对象 | 表现 | 倾向选择的身份 | 典型插入模式 |
| 共享记忆缺失 | 关键事实、约束或中间结论被多次产生，但后续 agent 没有稳定引用。 | Memory Prompt Node | source-consumer 插入；aggregator 前共享摘要。 |
| 答案冲突或错误风险 | 多个 agent 给出不一致答案，或者低可信输出被多次引用。 | Instruction / Verifier Prompt Node | 冲突中心插入；连接冲突双方、critic 和 aggregator。 |
| 局部规则或检查标准缺失 | 某个子任务需要固定格式、约束或评判标准，但原始 agent role 过泛。 | Instruction / Verifier Prompt Node | 局部 group 插入；只允许相关 agent 读写。 |
| 工具或资料使用缺口 | 多个 agent 需要同一工具说明、检索资料或 API 约束，重复询问导致成本高。 | Tool / Resource Prompt Node | 连接工具使用 agent 和工具调用链。 |
| 能力缺口或复杂临时职责 | 轻量提示无法完成所需推理、检索或工具调用，需要独立执行能力。 | Agent-like Prompt Node | 在任务缺口最明显的位置升级为真实智能体。 |
| 子图信息孤岛 | 两个子任务相关，但图结构上通信较弱，关键洞察停留在局部。 | 先选择合适身份，再采用 bridge 插入模式 | Memory 或 Verifier 放在两个弱通信子图之间；Bridge 不是身份类型。 |

## Table 7
| Selector 输出 | 含义 | 示例 |
| 节点身份 | 选择 Memory、Instruction / Verifier、Tool / Resource 或 Agent-like。 | 当前答案冲突明显，因此选择 Instruction / Verifier Prompt Node。 |
| 初始内容 | 节点最开始保存或执行的结构化提示。 | 列出冲突点、证据来源、证据强弱和待验证问题。 |
| 连接对象 | Prompt Node 与哪些 agent 或子图建边。 | 连接两个 solver、critic 和 aggregator；或连接数学组与代码组。 |
| 读写权限 | 哪些 agent 可以读取该节点，哪些输出可以写入该节点。 | 冲突双方和 aggregator 可读；产生新证据的 solver 可写入。 |
| 预算限制 | 限制节点长度、更新轮数或调用次数。 | 最多保留 120 个 token 的摘要，最多更新两轮。 |
| 预期作用 | 说明节点服务于错误抑制、洞察传播、共享记忆还是能力补足。 | Verifier 用于错误抑制；Memory 通过 bridge 插入模式传播关键洞察。 |

## Table 8
| 节点身份 | 更新重点 | 例子 |
| Memory Prompt Node | 保留被引用的事实、约束和推理，删除重复或过期历史。 | 把三轮讨论压缩成已确认事实、关键推理和待验证假设。 |
| Instruction / Verifier Prompt Node | 更新检查标准、冲突清单、证据强弱和已解决项。 | 记录哪个答案已被证据支持，哪个仍缺少依据。 |
| Tool / Resource Prompt Node | 更新工具参数、调用示例、资料摘要和失效信息。 | 当某个 API 参数被验证无效时，节点状态中标记并阻止重复调用。 |
| Agent-like Prompt Node | 更新子目标、推理摘要、工具调用结果和自身置信度。 | 当轻量节点被升级后，它保存独立推理结果并向相关 agent 返回摘要。 |

## Table 9
| 一致性类型 | 含义 | 用途 |
| 语义一致性 | agent 当前子任务与 Prompt Node 内容是否相关。 | 决定是否读取 Memory、Tool / Resource 或 bridge 插入位置上的节点。 |
| 冲突一致性 | agent 是否参与该节点记录的冲突或待验证问题。 | 决定是否读取 Instruction / Verifier。 |
| 可靠性一致性 | agent 的历史表现是否足够稳定，是否适合写入共享节点。 | 限制低可信 agent 写入 Memory 或共享检查结论。 |
| 预算一致性 | 这条读写或转发路径是否值得额外 token 成本。 | 控制是否转发压缩消息，避免所有 agent 阅读所有历史。 |
| 层级一致性 | 节点是否属于某个局部 group、任务阶段或子图边界。 | 控制局部共享范围，避免把 group 内部上下文全局广播。 |

## Table 10
| 当前状态 | 路由倾向 | Prompt Node 行为或生命周期动作 |
| 高冲突 / 低置信 | 偏向错误抑制。 | Instruction / Verifier 只发给冲突 agent 和 aggregator；低可信写入被限制。 |
| 关键洞察未传播 | 偏向洞察传播。 | Memory 通过 bridge 插入模式把压缩洞察转发给相关 agent。 |
| 通信冗余高 | 压缩后转发。 | Memory 替代重复历史；路由行为阻止低价值长消息继续广播。 |
| 子任务强相关但图上距离远 | 建立局部定向连接。 | 选择合适身份的 Prompt Node 放在两个子图之间，而不是把两个子图全连接。 |
| 节点贡献低 | 剪枝或删除。 | 若长期未被引用、未提升结果且增加成本，则删除节点或剪掉相关边。 |
| 节点反复承担复杂推理或工具调用 | 升级。 | 将轻量 Prompt Node 升级为 Agent-like 节点，允许其独立推理或调用工具。 |

## Table 11
| 实验部分 | 简要设计 |
| Baseline | Single Agent、Chain / Full / Random MAS、AgentPrune、AgentDropout、EIB-Learner、ARG / ADG-DESIGNER、GoAgent。 |
| 任务 | 先选数学推理、多跳问答和代码生成中的 2-3 类任务，优先选择容易观察冲突和关键洞察传播的 benchmark。 |
| 指标 | Accuracy 或 pass@k、总 token、冲突解决率、关键洞察引用率、错误注入后的性能下降、Prompt Node 贡献率。 |
| 消融 | 去掉 Prompt Node、去掉动态更新、去掉路由控制、只保留 Memory / Verifier / Agent-like、随机插入 Prompt Node。 |
| Case Study | 展示一个冲突被 Verifier 抑制、一个关键洞察经 Memory bridge 传播、一个轻量节点被升级为 Agent-like 的例子。 |
