# ## 21. Explicabilidad — SHAP

# %%
pipe_final = finales[H]
idx_te = ite[ite].index
Xt = pipe_final.named_steps['prep'].transform(X.loc[idx_te, ALL_COLS])
nombres = [n.split('__')[1] for n in pipe_final.named_steps['prep'].get_feature_names_out()]
explainer = shap.TreeExplainer(pipe_final.named_steps['modelo'])
sv = explainer.shap_values(Xt)
imp = pd.Series(np.abs(sv).mean(0), index=nombres)
imp_mes = imp[[c for c in nombres if c.startswith('mes_')]].sum()
imp = pd.concat([imp[[c for c in nombres if not c.startswith('mes_')]], pd.Series({'mes (total)': imp_mes})]).sort_values()
R['shap'] = imp.sort_values(ascending=False).round(5).to_dict()
fig, ax = plt.subplots(figsize=(6, 5))
ax.barh(imp.index, imp.values, color=[C_P if c.startswith(('P', 'API')) else C_OBS for c in imp.index], height=0.7)
ax.set_xlabel('|SHAP| medio (Δlog Q)'); ax.grid(axis='y', visible=False)
ax.set_title('Importancia de variables (verde: lluvia · azul: caudal)', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/shap_importancia.png', dpi=150); plt.show()

# %%
shap.summary_plot(sv, Xt, feature_names=nombres, max_display=12, show=False)
plt.tight_layout(); plt.savefig(f'{FIG}/shap_resumen.png', dpi=150); plt.show()

# %%
# Dependencia: efecto de P10 según la tendencia del caudal
i_p10, i_dq = nombres.index('P10'), nombres.index('dlQ_1')
fig, ax = plt.subplots(figsize=(6.5, 4))
sc = ax.scatter(X.loc[idx_te, 'P10'], sv[:, i_p10], c=X.loc[idx_te, 'dlQ_1'].clip(-0.15, 0.15), cmap='coolwarm', s=7, alpha=0.7)
plt.colorbar(sc, ax=ax, label='dlQ_1 (tendencia del último día)')
ax.set_xlabel('P10: lluvia acumulada de 10 días (mm)'); ax.set_ylabel('Contribución SHAP de P10 (Δlog Q)')
ax.set_title('Cómo influye la lluvia de 10 días en el pronóstico', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/shap_dependencia_P10.png', dpi=150); plt.show()
