import os
import pandas as pd


def evaluation(routing_results_df):
    print("[5/7] Evaluating KPIs across Scenarios...")

    if routing_results_df is None or routing_results_df.empty:
        print("  -> [!] Bỏ qua đánh giá KPI vì không có dữ liệu Routing.")
        return None

    results_out = {}

    for strategy in routing_results_df['hub_strategy'].unique():
        df_s = routing_results_df[routing_results_df['hub_strategy'] == strategy]

        summary = df_s.groupby(['traffic_condition', 'scenario']).agg(
            avg_time_min    = ('time',     'mean'),
            total_distance_km = ('distance', 'sum'),
            avg_distance_km = ('distance', 'mean'),
            total_cost_vnd  = ('cost',     'sum'),
            avg_cost_vnd    = ('cost',     'mean'),
            total_co2_kg    = ('co2',      'sum'),
            avg_co2_kg      = ('co2',      'mean'),
            delivery_count  = ('order_id', 'count'),
            multimodal_used = ('modes_used', lambda x: (x != 'road').sum()),
        ).reset_index()

        for col in summary.columns:
            if summary[col].dtype == 'float64':
                summary[col] = summary[col].round(2)

        # Tính % cải thiện so với baseline (Road Only)
        improvement_rows = []
        for traffic in summary['traffic_condition'].unique():
            df_t  = summary[summary['traffic_condition'] == traffic]
            baseline_row = df_t[df_t['scenario'].str.contains('Road Only')]
            if baseline_row.empty:
                continue
            b_time = baseline_row['avg_time_min'].values[0]
            b_co2  = baseline_row['total_co2_kg'].values[0]
            b_cost = baseline_row['total_cost_vnd'].values[0]
            for _, row in df_t.iterrows():
                pct_time = round((b_time - row['avg_time_min']) / b_time * 100, 1) if b_time else 0
                pct_co2  = round((b_co2  - row['total_co2_kg'])  / b_co2  * 100, 1) if b_co2  else 0
                pct_cost = round((b_cost - row['total_cost_vnd']) / b_cost * 100, 1) if b_cost else 0
                improvement_rows.append({
                    'hub_strategy':        strategy,
                    'traffic_condition':   traffic,
                    'scenario':            row['scenario'],
                    'avg_time_min':        row['avg_time_min'],
                    'total_co2_kg':        row['total_co2_kg'],
                    'avg_cost_vnd':        row['avg_cost_vnd'],
                    'multimodal_used_cnt': row['multimodal_used'],
                    'time_improvement_pct': pct_time,
                    'co2_improvement_pct':  pct_co2,
                    'cost_improvement_pct': pct_cost,
                })

        df_improve = pd.DataFrame(improvement_rows)
        results_out[strategy] = {'summary': summary, 'improvement': df_improve}

        print(f"\n  === [{strategy.upper()}] KPI SUMMARY ===")
        print(summary[['traffic_condition','scenario','avg_time_min','total_co2_kg','avg_cost_vnd','multimodal_used','delivery_count']].to_string(index=False))
        print(f"\n  === [{strategy.upper()}] % CẢI THIỆN SO VỚI ROAD ONLY ===")
        if not df_improve.empty:
            print(df_improve[df_improve['scenario'] != df_improve['scenario'].str.contains('Road Only').map({True:'x',False:'y'})][
                ['traffic_condition','scenario','time_improvement_pct','co2_improvement_pct','cost_improvement_pct']
            ].to_string(index=False))

    # Gộp tất cả summary và improvement để lưu file
    all_summary = pd.concat([v['summary'].assign(hub_strategy=k) for k, v in results_out.items()], ignore_index=True)
    all_improve = pd.concat([v['improvement'] for v in results_out.values()], ignore_index=True)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    all_summary.to_csv(os.path.join(results_dir, "summary_results.csv"), index=False)
    all_improve.to_csv(os.path.join(results_dir, "improvement_results.csv"), index=False)
    print("\n  -> KPIs saved to results/summary_results.csv")
    print("  -> Improvement table saved to results/improvement_results.csv")

    try:
        with pd.ExcelWriter(os.path.join(results_dir, "summary_results.xlsx"), engine="openpyxl") as writer:
            for strategy, data in results_out.items():
                sheet = strategy[:28]  # Excel giới hạn 31 ký tự sheet name
                data['summary'].to_excel(writer, index=False, sheet_name=f"KPI_{sheet}")
                data['improvement'].to_excel(writer, index=False, sheet_name=f"Improve_{sheet}")
        print("  -> Excel report saved to results/summary_results.xlsx")
    except Exception as e:
        print(f"  -> [!] Excel warning: {e}")

    return results_out.get('nearest', {}).get('summary')