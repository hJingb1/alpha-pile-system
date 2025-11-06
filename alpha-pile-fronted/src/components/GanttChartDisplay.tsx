// // src/components/GanttChartDisplay.tsx
// import React, { useEffect, useRef } from 'react';
// import Gantt from 'frappe-gantt';

// // --- 使用项目自定义的 CSS (根据你之前的截图信息) ---
// // 确保这个路径是正确的，并且 src/styles/gantt.css 和它可能依赖的 light.css 都存在且内容正确
// // import '../../styles/gantt.css'; 

// interface TaskInfo {
//     pile_id: number | string;
//     start_hour: number;
//     end_hour: number;
//     duration_hour: number;
//     machine: number;
//     x: number;
//     y: number;
//     type: number;
// }

// interface GanttChartDisplayProps {
//   schedule: TaskInfo[];
// }

// const convertHourToDateString = (hours: number): string => {
//     const baseDate = new Date(2024, 0, 1); // 0 代表一月
//     const targetDate = new Date(baseDate.getTime() + hours * 60 * 60 * 1000);
//     const year = targetDate.getFullYear();
//     const month = String(targetDate.getMonth() + 1).padStart(2, '0');
//     const day = String(targetDate.getDate()).padStart(2, '0');
//     return `${year}-${month}-${day}`;
// };

// // --- 定义符合 frappe-gantt 文档的 ViewModeObject (如果需要自定义 view_modes) ---
// // Frappe Gantt 的 view_modes 期望一个对象数组，每个对象可以有 name, padding, step 等属性
// // 如果只是想用默认的视图模式，并让用户切换，可以不提供 view_modes，只提供 view_mode
// // 如果你想自定义每个视图模式的显示细节（如头部文本格式），才需要详细定义 view_modes

// const GanttChartDisplay: React.FC<GanttChartDisplayProps> = ({ schedule }) => {
//   const ganttRef = useRef<SVGSVGElement | null>(null);
//   const ganttInstance = useRef<Gantt | null>(null);

//   useEffect(() => {
//     console.log("GanttChartDisplay received schedule prop:", JSON.stringify(schedule, null, 2));
//     if (ganttRef.current && schedule && schedule.length > 0) {
//       const tasks = schedule.map((task, index) => ({
//         id: `task_${task.pile_id}_${index}`,
//         name: `桩 ${task.pile_id}`, // frappe-gantt 会显示这个 name
//         start: convertHourToDateString(task.start_hour),
//         end: convertHourToDateString(task.end_hour),
//         progress: 100, // 假设任务已规划完成
//         custom_class: `machine-${task.machine || 'unknown'}` // 用于自定义样式
//       }));

//       console.log("Data dynamically passed to Frappe Gantt:", JSON.stringify(tasks, null, 2));

//       if (ganttInstance.current) {
//         ganttInstance.current.clear();
//         if (ganttRef.current) {
//           ganttRef.current.innerHTML = '';
//         }
//       }

//       try {
//         ganttInstance.current = new Gantt(ganttRef.current, tasks, {
//           // --- 基于 README 调整的选项 ---
//           // header_height: 50,        // 你可以根据需要调整，或者用默认的 (注释掉此行)
//           upper_header_height: 45, // README 中有此选项，可以保留
//           lower_header_height: 30, // README 中有此选项，可以保留
//           bar_height: 18,
//           padding: 12,             // 任务条之间的垂直间距
          
//           view_mode: 'Day',       // 初始视图模式 ('Day', 'Week', 'Month', 'Year')
//           // view_modes: undefined, // 如果你不想自定义 view_modes 数组，可以不传或传 undefined，它会使用默认的
//                                   // 如果想让用户能切换视图，但使用默认的视图模式，可以不设置此项，
//                                   // 然后通过 view_mode_select: true (如果库支持此选项，或 UI 上自己实现切换按钮调用 .change_view_mode())
          
//           date_format: 'YYYY-MM-DD', // 与你的 convertHourToDateString 格式一致
//           language: 'zh',          // 尝试中文，如果显示不正确，先换回 'en' 测试
          
//           // --- 其他常用选项 (根据README) ---
//           // arrow_curve: 5,
//           // bar_corner_radius: 3,
//           // column_width: 45, // 默认是45，你可以调整
//           // lines: 'both', // 显示网格线
//           popup_on: 'click', // 点击任务条时显示弹窗 (如果 custom_popup_html 未配置，会显示默认弹窗)
//           // custom_popup_html: (task) => { // 自定义弹窗内容
//           //   return `
//           //     <div class="title">${task.name}</div>
//           //     <div class="subtitle">
//           //       开始: ${task.start} <br>
//           //       结束: ${task.end}
//           //     </div>
//           //   `;
//           // },
          
//           // on_progress_change: (task, progress) => { console.log("Progress changed:", task, progress); }, // 修改进度后的回调
//         });
//       } catch (error) {
//         console.error("Failed to initialize Gantt chart:", error);
//       }

//     } else if (ganttRef.current) {
//       // 清空逻辑
//       if (ganttInstance.current) {
//         ganttInstance.current.clear();
//         ganttInstance.current = null;
//       }
//       ganttRef.current.innerHTML = '';
//       const noDataMessage = document.createElementNS("http://www.w3.org/2000/svg", "text");
//       noDataMessage.setAttribute("x", "50%");
//       noDataMessage.setAttribute("y", "50%");
//       noDataMessage.setAttribute("text-anchor", "middle");
//       noDataMessage.textContent = "无调度数据可显示";
//       ganttRef.current.appendChild(noDataMessage);
//     }
//   }, [schedule]);

//   return (
//     <div 
//         style={{ 
//             overflow: 'auto', // 允许容器自身滚动
//             border: '1px solid #eee',
//             height: '600px',    // 给一个明确的高度
//             width: '100%'       
//         }}
//     >
//         <svg ref={ganttRef}></svg>
//     </div>
//   );
// };

// export default GanttChartDisplay;