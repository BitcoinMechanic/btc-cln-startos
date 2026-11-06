# Keep official 26.06.10 Rust plugins; rebuild the complete C runtime with the
# audited swap-safety patch. Configure still enables the full builtin list.
.PHONY: install-c-runtime
install-c-runtime: installdirs $(BIN_PROGRAMS) $(PKGLIBEXEC_PROGRAMS) $(C_PLUGINS)
	$(INSTALL_PROGRAM) $(BIN_PROGRAMS) $(DESTDIR)$(bindir)
	$(INSTALL_PROGRAM) $(PKGLIBEXEC_PROGRAMS) $(DESTDIR)$(pkglibexecdir)
	$(INSTALL_PROGRAM) $(C_PLUGINS) $(DESTDIR)$(plugindir)
