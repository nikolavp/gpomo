APP=gpomo
BIN=/usr/bin/gpomo
BASE=/usr/share/pyshared/$(APP)
LIB=$(BASE)/lib/
MANAGERS=$(BASE)/lib/managers/
IMAGES=$(BASE)/images/
LOCALE=/usr/share
MO_INSTALL=$(shell find -iname '*.mo' -exec sh -c "dirname {} | cut -b2-" \;)
MO_REMOVE=$(shell find $(LOCALE)/locale/ -iname '$(APP).mo')

install:
	mkdir -p $(LIB)
	mkdir -p $(MANAGERS)
	mkdir -p $(IMAGES)
	cp *.py $(LIB)
	cp lib/managers/*.py $(MANAGERS)
	rm -f $(BIN)
	ln -s $(LIB)/gpomo.py $(BIN) 
	cp images/* $(IMAGES)
	@for TRANSLATION in $(MO_INSTALL); do \
		echo "Installing $${TRANSLATION}"; \
		cp .$${TRANSLATION}/$(APP).mo $(LOCALE)$${TRANSLATION}/$(APP).mo; \
	done

uninstall:
	rm -f $(MANAGERS)/*
	rmdir $(MANAGERS)
	rm -f $(BIN)
	rm -f $(LIB)/*
	rm -f $(IMAGES)/*
	rmdir $(LIB)
	rmdir $(IMAGES)
	rmdir $(BASE)
	@for TRANSLATION in $(MO_REMOVE); do \
		echo "Removing $${TRANSLATION}"; \
		rm $${TRANSLATION}; \
	done
